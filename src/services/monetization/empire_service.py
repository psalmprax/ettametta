import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from src.api.utils.models import SocialAccount, PublishedContentDB, VideoJobDB
from typing import Any


class EmpireService:
    def get_empire_metrics(self, db: Session, user_id: str) -> dict[str, Any]:
        """
        Aggregates real cross-account performance metrics with growth velocity.
        """
        import datetime

        now = datetime.datetime.now(datetime.timezone.utc)
        last_week = now - datetime.timedelta(days=7)
        prev_week = now - datetime.timedelta(days=14)

        # 1. Total Accounts
        account_count = (
            db.query(SocialAccount).filter(SocialAccount.user_id == user_id).count()
        )

        # 2. Growth Calculation (Comparison of week-over-week views)
        current_week_views = (
            db.query(func.sum(PublishedContentDB.view_count))
            .filter(
                PublishedContentDB.user_id == user_id,
                PublishedContentDB.published_at >= last_week,
            )
            .scalar()
            or 0
        )

        previous_week_views = (
            db.query(func.sum(PublishedContentDB.view_count))
            .filter(
                PublishedContentDB.user_id == user_id,
                PublishedContentDB.published_at >= prev_week,
                PublishedContentDB.published_at < last_week,
            )
            .scalar()
            or 0
        )

        total_growth = 0
        if previous_week_views > 0:
            total_growth = (
                (current_week_views - previous_week_views) / previous_week_views
            ) * 100

        # 3. Performance by Niche/Node
        niche_stats = (
            db.query(
                PublishedContentDB.platform,
                func.sum(PublishedContentDB.view_count).label("total_views"),
                func.count(PublishedContentDB.id).label("post_count"),
            )
            .filter(PublishedContentDB.user_id == user_id)
            .group_by(PublishedContentDB.platform)
            .all()
        )

        velocity_data = []
        for stat in niche_stats:
            vpp = stat.total_views / stat.post_count if stat.post_count > 0 else 0
            # Normalized score based on views per post (maxed at 100)
            score = int(min(vpp / 10, 100))
            velocity_data.append(
                {
                    "name": f"{stat.platform}_Node",
                    "growth": f"+{total_growth:.1f}%"
                    if total_growth >= 0
                    else f"{total_growth:.1f}%",
                    "score": score,
                }
            )

        return {
            "account_count": account_count,
            "velocity": velocity_data,
            "total_growth": total_growth,
        }

    def get_network_graph(self, db: Session, user_id: str) -> dict[str, list[Any]]:
        """
        Generates a D3-compatible network graph of the user's empire.
        Queries real data from PublishedContentDB and monitored niches.
        """
        # Fetch user's published content to build real network
        published = (
            db.query(PublishedContentDB)
            .filter(PublishedContentDB.user_id == user_id)
            .all()
        )

        # Fetch monitored niches for the user
        from src.api.utils.models import MonitoredNiche

        niches = (
            db.query(MonitoredNiche)
            .filter(MonitoredNiche.user_id == user_id, MonitoredNiche.is_active == True)
            .all()
        )

        # Build nodes from real data
        nodes = []
        links = []

        # Root node
        nodes.append({"id": "root", "group": 1, "label": "Empire Core"})

        # Add niche nodes
        niche_index = 1
        for niche in niches[:5]:  # Limit to 5 niches
            niche_id = f"strat_{niche_index}"
            nodes.append(
                {
                    "id": niche_id,
                    "group": 2,
                    "label": niche.niche
                    if hasattr(niche, "niche")
                    else f"Niche {niche_index}",
                }
            )
            links.append({"source": "root", "target": niche_id, "value": 10})
            niche_index += 1

        # Add content nodes (published videos)
        content_index = 1
        for content in published[:10]:  # Limit to 10 most recent
            content_id = f"content_{content_index}"
            platform = content.platform if hasattr(content, "platform") else "Unknown"
            nodes.append(
                {"id": content_id, "group": 3, "label": f"{platform}_{content.id[:8]}"}
            )
            # Link to first niche or root
            target = f"strat_{content_index}" if content_index < niche_index else "root"
            links.append({"source": target, "target": content_id, "value": 5})
            content_index += 1

        # If no real data, return gateway cluster topology
        if len(nodes) <= 1:
            # Add master gateway node
            nodes.append(
                {
                    "id": "gateway_1",
                    "group": 1,
                    "label": "149.104.110.122",
                    "status": "ONLINE",
                }
            )
            links.append({"source": "root", "target": "gateway_1", "value": 20})

            # Add default service nodes
            nodes.append({"id": "api", "group": 2, "label": "API Core"})
            nodes.append({"id": "dashboard", "group": 2, "label": "Dashboard"})
            nodes.append({"id": "discovery", "group": 2, "label": "Discovery Engine"})
            nodes.append({"id": "worker_1", "group": 3, "label": "Video Worker"})

            links.append({"source": "gateway_1", "target": "api", "value": 10})
            links.append({"source": "gateway_1", "target": "dashboard", "value": 10})
            links.append({"source": "gateway_1", "target": "discovery", "value": 10})
            links.append({"source": "api", "target": "worker_1", "value": 5})

        return {"nodes": nodes, "links": links}

    def get_winning_blueprints(self, db: Session, user_id: str) -> list[dict[str, Any]]:
        """
        Fetches proven patterns from A/B test winners to serve as "blueprints".
        """
        from src.api.utils.models import ABTestDB

        # Query A/B tests with confirmed winners
        winning_tests = (
            db.query(ABTestDB)
            .filter(ABTestDB.winner_variant != None)
            .order_by(ABTestDB.created_at.desc())
            .limit(10)
            .all()
        )

        blueprints = []
        for test in winning_tests:
            winner_title = (
                test.variant_a_title
                if test.winner_variant == "A"
                else test.variant_b_title
            )
            blueprints.append(
                {
                    "id": f"ab_{test.id}",
                    "title": winner_title,
                    "niche": "Pattern Proved via A/B",
                    "performance": f"{max(test.variant_a_view_count, test.variant_b_view_count)} views",
                    "status": "A/B Data Validated",
                }
            )

        # Fallback to high-performing content if not enough A/B tests
        if len(blueprints) < 5:
            top_posts = (
                db.query(PublishedContentDB)
                .filter(PublishedContentDB.user_id == user_id)
                .order_by(PublishedContentDB.view_count.desc())
                .limit(5)
                .all()
            )

            for post in top_posts:
                blueprints.append(
                    {
                        "id": f"post_{post.id}",
                        "title": f"Viral Node {post.platform}",
                        "niche": post.niche,
                        "performance": f"{post.view_count} views",
                        "status": "Verified Reach",
                    }
                )

        return blueprints[:10]

    async def clone_strategy(
        self,
        db: Session,
        user_id: str,
        source_niche: str,
        target_niche: str,
        auto_publish: bool = False,
    ) -> bool:
        """
        Clones system settings/parameters from a source niche to a target niche.
        Copies:
        - MonitoredNiche entry (if target doesn't exist)
        - All affiliate links for the source niche to the target niche
        - Any user settings that are niche-specific (key = niche:*)
        Returns True if successful.
        """
        from src.api.utils.models import MonitoredNiche, AffiliateLinkDB, UserSetting
        import datetime

        logging.info(
            f"[Empire] User {user_id} cloning strategy: {source_niche} -> {target_niche}"
        )

        try:
            # 1. Ensure source niche exists (if not, cannot clone)
            source_monitored = (
                db.query(MonitoredNiche)
                .filter(
                    MonitoredNiche.user_id == user_id,
                    MonitoredNiche.niche == source_niche,
                )
                .first()
            )

            if not source_monitored:
                logging.warning(
                    f"[Empire] Source niche '{source_niche}' not monitored by user {user_id}"
                )
                return False

            # 2. Create or update target MonitoredNiche
            target_monitored = (
                db.query(MonitoredNiche)
                .filter(
                    MonitoredNiche.user_id == user_id,
                    MonitoredNiche.niche == target_niche,
                )
                .first()
            )

            if not target_monitored:
                target_monitored = MonitoredNiche(
                    user_id=user_id, niche=target_niche, is_active=True
                )
                db.add(target_monitored)
            else:
                # Anyly activate if was inactive
                target_monitored.is_active = True

            # 3. Copy affiliate links from source niche to target niche
            # First, check which affiliate links belong to source_niche
            existing_links = (
                db.query(AffiliateLinkDB)
                .filter(
                    AffiliateLinkDB.user_id == user_id,
                    AffiliateLinkDB.niche == source_niche,
                )
                .all()
            )

            for link in existing_links:
                # Check if a similar link already exists in target to avoid duplicates
                existing_target_link = (
                    db.query(AffiliateLinkDB)
                    .filter(
                        AffiliateLinkDB.user_id == user_id,
                        AffiliateLinkDB.niche == target_niche,
                        AffiliateLinkDB.product_name == link.product_name,
                        AffiliateLinkDB.link == link.link,
                    )
                    .first()
                )

                if not existing_target_link:
                    new_link = AffiliateLinkDB(
                        user_id=user_id,
                        niche=target_niche,
                        product_name=link.product_name,
                        link=link.link,
                        cta_text=link.cta_text,
                    )
                    db.add(new_link)

            # 4. Copy niche-specific user settings (if any)
            # Settings with key pattern "niche:{niche}:*" are considered niche-specific
            niche_setting_prefix = f"niche:{source_niche}:"
            source_settings = (
                db.query(UserSetting)
                .filter(
                    UserSetting.user_id == user_id,
                    UserSetting.key.like(f"{niche_setting_prefix}%"),
                )
                .all()
            )

            for setting in source_settings:
                new_key = setting.key.replace(
                    f"niche:{source_niche}:", f"niche:{target_niche}:"
                )
                existing_target_setting = (
                    db.query(UserSetting)
                    .filter(UserSetting.user_id == user_id, UserSetting.key == new_key)
                    .first()
                )

                if not existing_target_setting:
                    new_setting = UserSetting(
                        user_id=user_id,
                        key=new_key,
                        value=setting.value,
                        category=setting.category,
                    )
                    db.add(new_setting)

            db.commit()
            logging.info(
                f"[Empire] Strategy cloned successfully: {len(existing_links)} affiliate links, niche settings copied"
            )
            return True

        except Exception as e:
            db.rollback()
            logging.error(f"[Empire] Clone strategy failed: {e}")
            return False

    async def get_activity_stream(
        self, db: Session, user_id: str
    ) -> list[dict[str, Any]]:
        """
        Aggregates real system and monetization events into a single timeline.
        Transitions from simulation to real telemetry.
        """
        import datetime
        from src.api.utils.models import (
            PublishedContentDB,
            AffiliateLinkDB,
            RevenueLogDB,
            SystemActivityDB,
        )

        events = []

        # 1. Recent Publications
        recent_posts = (
            db.query(PublishedContentDB)
            .filter(PublishedContentDB.user_id == user_id)
            .order_by(PublishedContentDB.published_at.desc())
            .limit(10)
            .all()
        )
        for post in recent_posts:
            events.append(
                {
                    "id": f"post_{post.id}",
                    "timestamp": post.published_at.isoformat(),
                    "time_label": post.published_at.strftime("%H:%M ZULU"),
                    "type": "NODE_EXPANSION",
                    "message": f"Successfully expanded network to {post.platform}: {post.title[:30]}...",
                    "status": "SUCCESS",
                }
            )

        # 2. Revenue Logs
        recent_rev = (
            db.query(RevenueLogDB)
            .filter(RevenueLogDB.user_id == user_id)
            .order_by(RevenueLogDB.date.desc())
            .limit(5)
            .all()
        )
        for rev in recent_rev:
            events.append(
                {
                    "id": f"rev_{rev.id}",
                    "timestamp": rev.date.isoformat(),
                    "time_label": rev.date.strftime("%H:%M ZULU"),
                    "type": "REVENUE_ACHIEVEMENT",
                    "message": f"Revenue milestone reached on {rev.platform}: ${rev.amount:,.2f}",
                    "status": "SUCCESS",
                }
            )

        # 3. New Affiliate Links
        recent_links = (
            db.query(AffiliateLinkDB)
            .filter(AffiliateLinkDB.user_id == user_id)
            .order_by(AffiliateLinkDB.created_at.desc())
            .limit(5)
            .all()
        )
        for link in recent_links:
            events.append(
                {
                    "id": f"link_{link.id}",
                    "timestamp": link.created_at.isoformat(),
                    "time_label": link.created_at.strftime("%H:%M ZULU"),
                    "type": "STRATEGY_DEPLOYMENT",
                    "message": f"New monetization node active: {link.product_name} ({link.niche})",
                    "status": "SUCCESS",
                }
            )

        # 4. Global Sentinel Events (Module Broad)
        sentinel_logs = (
            db.query(SystemActivityDB)
            .filter(SystemActivityDB.module == "SENTINEL")
            .order_by(SystemActivityDB.created_at.desc())
            .limit(5)
            .all()
        )
        for log in sentinel_logs:
            events.append(
                {
                    "id": f"sys_{log.id}",
                    "timestamp": log.created_at.isoformat(),
                    "time_label": log.created_at.strftime("%H:%M ZULU"),
                    "type": "SENTINEL_SHIFT",
                    "message": log.message,
                    "status": log.level,
                }
            )

        # Final Sorting & Limiting
        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events[:15]


base_empire_service = EmpireService()
