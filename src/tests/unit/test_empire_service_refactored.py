import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session


@pytest.fixture
def mock_db():
    db = MagicMock(spec=Session)
    return db


@pytest.fixture
def empire_service():
    from src.services.monetization.empire_service import EmpireService
    return EmpireService()


class TestGetEmpireMetrics:
    def test_returns_account_count(self, empire_service, mock_db):
        mock_db.scalar.return_value = 5
        mock_db.execute.return_value.all.return_value = []
        result = empire_service.get_empire_metrics(mock_db, "user-1")
        assert result["account_count"] == 5

    def test_calculates_total_growth(self, empire_service, mock_db):
        now = datetime.now(timezone.utc)
        now - timedelta(days=7)
        now - timedelta(days=14)
        mock_db.scalar.side_effect = [
            3,                         # account_count
            1000,                      # current_week_views
            500,                       # previous_week_views
        ]
        mock_db.execute.return_value.all.return_value = []
        result = empire_service.get_empire_metrics(mock_db, "user-1")
        assert result["total_growth"] == 100.0

    def test_growth_zero_when_no_previous(self, empire_service, mock_db):
        mock_db.scalar.side_effect = [2, 100, 0]
        mock_db.execute.return_value.all.return_value = []
        result = empire_service.get_empire_metrics(mock_db, "user-1")
        assert result["total_growth"] == 0

    def test_velocity_data(self, empire_service, mock_db):
        mock_db.scalar.side_effect = [1, 200, 100]
        stat = MagicMock(platform="youtube", total_views=200, post_count=2)
        mock_db.execute.return_value.all.return_value = [stat]
        result = empire_service.get_empire_metrics(mock_db, "user-1")
        assert len(result["velocity"]) == 1
        assert result["velocity"][0]["name"] == "youtube_Node"
        assert result["velocity"][0]["score"] == 10


class TestGetNetworkGraph:
    def test_empty_graph_uses_gateway(self, empire_service, mock_db):
        mock_db.scalars.return_value.all.return_value = []
        with patch("src.services.monetization.empire_service.settings") as mock_s:
            mock_s.GATEWAY_HOST = "my-gateway.example.com"
            result = empire_service.get_network_graph(mock_db, "user-1")
        assert len(result["nodes"]) > 1
        assert result["nodes"][1]["label"] == "my-gateway.example.com"

    def test_nonempty_graph(self, empire_service, mock_db):
        niche = MagicMock(niche="crypto")
        niche.id = "n1"
        content = MagicMock(platform="youtube", id="c1")
        content.id = "c1"
        mock_db.scalars.side_effect = [
            MagicMock(all=MagicMock(return_value=[content])),
            MagicMock(all=MagicMock(return_value=[niche])),
        ]
        result = empire_service.get_network_graph(mock_db, "user-1")
        assert any(n["id"] == "root" for n in result["nodes"])
        assert any(n["label"] == "crypto" for n in result["nodes"])


class TestGetWinningBlueprints:
    def test_ab_test_blueprints(self, empire_service, mock_db):
        test = MagicMock()
        test.id = "t1"
        test.winner_variant = "A"
        test.variant_a_title = "Title A"
        test.variant_b_title = "Title B"
        test.variant_a_view_count = 500
        test.variant_b_view_count = 300
        mock_db.scalars.side_effect = [
            MagicMock(all=MagicMock(return_value=[test])),
        ]
        result = empire_service.get_winning_blueprints(mock_db, "user-1")
        assert len(result) == 1
        assert result[0]["title"] == "Title A"

    def test_ab_test_fallback_to_posts(self, empire_service, mock_db):
        post = MagicMock(id="p1", platform="tiktok", niche="fitness", view_count=1000)
        mock_db.scalars.side_effect = [
            MagicMock(all=MagicMock(return_value=[])),   # no A/B tests
            MagicMock(all=MagicMock(return_value=[post])),
        ]
        result = empire_service.get_winning_blueprints(mock_db, "user-1")
        assert len(result) == 1
        assert result[0]["title"] == "Viral Node tiktok"

    def test_ab_test_query_exception(self, empire_service, mock_db):
        mock_db.scalars.side_effect = [
            Exception("db error"),
            MagicMock(all=MagicMock(return_value=[])),
        ]
        result = empire_service.get_winning_blueprints(mock_db, "user-1")
        assert result == []


class TestCloneStrategy:
    @pytest.mark.asyncio
    async def test_clone_returns_false_if_no_source(self, empire_service, mock_db):
        mock_db.scalars.side_effect = [MagicMock(first=MagicMock(return_value=None))]
        result = await empire_service.clone_strategy(mock_db, "user-1", "crypto", "fitness")
        assert result is False

    @pytest.mark.asyncio
    async def test_clone_creates_target_niche(self, empire_service, mock_db):
        source = MagicMock()
        mock_db.scalars.side_effect = [
            MagicMock(first=MagicMock(return_value=source)),   # source niche
            MagicMock(first=MagicMock(return_value=None)),     # target niche
            MagicMock(all=MagicMock(return_value=[])),          # affiliate links
            MagicMock(all=MagicMock(return_value=[])),          # source settings
        ]
        result = await empire_service.clone_strategy(mock_db, "user-1", "crypto", "fitness")
        assert result is True
        mock_db.add.assert_called()
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_clone_exception_returns_false(self, empire_service, mock_db):
        mock_db.scalars.side_effect = Exception("db error")
        result = await empire_service.clone_strategy(mock_db, "user-1", "a", "b")
        assert result is False
        mock_db.rollback.assert_called_once()


class TestGetActivityStream:
    @pytest.mark.asyncio
    async def test_empty_stream(self, empire_service, mock_db):
        mock_db.scalars.return_value.all.return_value = []
        result = await empire_service.get_activity_stream(mock_db, "user-1")
        assert result == []

    @pytest.mark.asyncio
    async def test_mixed_events_sorted(self, empire_service, mock_db):
        now = datetime.now(timezone.utc)
        post = MagicMock(id="p1", published_at=now, title="My Post", platform="youtube")
        rev = MagicMock(id="r1", date=now - timedelta(hours=1), platform="youtube", amount=42.50)
        link = MagicMock(id="l1", created_at=now + timedelta(minutes=30), product_name="Widget", niche="tech")
        sentinel = MagicMock(id="s1", created_at=now - timedelta(minutes=10), message="Threat detected", level="WARNING")

        mock_db.scalars.side_effect = [
            MagicMock(all=MagicMock(return_value=[post])),
            MagicMock(all=MagicMock(return_value=[rev])),
            MagicMock(all=MagicMock(return_value=[link])),
            MagicMock(all=MagicMock(return_value=[sentinel])),
        ]
        result = await empire_service.get_activity_stream(mock_db, "user-1")
        assert len(result) == 4
        timestamps = [e["timestamp"] for e in result]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_partial_failure_continues(self, empire_service, mock_db):
        now = datetime.now(timezone.utc)
        link = MagicMock(id="l1", created_at=now, product_name="X", niche="a")
        mock_db.scalars.side_effect = [
            Exception("posts failed"),
            MagicMock(all=MagicMock(return_value=[])),
            MagicMock(all=MagicMock(return_value=[link])),
            Exception("sentinel failed"),
        ]
        result = await empire_service.get_activity_stream(mock_db, "user-1")
        assert len(result) == 1
        assert result[0]["type"] == "STRATEGY_DEPLOYMENT"
