import logging
from sqlalchemy.orm import Session
from sqlalchemy import func, select
from src.api.utils.models import (
    SocialAccount,
    PublishedContentDB,
    MonitoredNiche,
    ABTestDB,
    AffiliateLinkDB,
    UserSetting,
    RevenueLogDB,
    SystemActivityDB,
)
from src.api.config import settings
from typing import Any


class EmpireService:
    def get_empire_metrics(self, db: Session, user_id: str) -> dict[str, Any]:
        import datetime

        now = datetime.datetime.now(datetime.timezone.utc)
        last_week = now - datetime.timedelta(days=7)
        prev_week = now - datetime.timedelta(days=14)

        account_count = db.scalar(
            select(func.count()).where(SocialAccount.user_id == user_id)
        )

        current_week_views = (
            db.scalar(
                select(func.sum(PublishedContentDB.view_count)).where(
                    PublishedContentDB.user_id == user_id,
                    PublishedContentDB.published_at >= last_week,
                )
            )
            or 0
        )

        previous_week_views = (
            db.scalar(
                select(func.sum(PublishedContentDB.view_count)).where(
                    PublishedContentDB.user_id == user_id,
                    PublishedContentDB.published_at >= prev_week,
                    PublishedContentDB.published_at < last_week,
                )
            )
            or 0
        )

        total_growth = 0
        if previous_week_views > 0:
            total_growth = (
                (current_week_views - previous_week_views) / previous_week_views
            ) * 100

        niche_stats = db.execute(
            select(
                PublishedContentDB.platform,
                func.sum(PublishedContentDB.view_count).label("total_views"),
                func.count(PublishedContentDB.id).label("post_count"),
            )
            .where(PublishedContentDB.user_id == user_id)
            .group_by(PublishedContentDB.platform)
        ).all()

        velocity_data = []
        for stat in niche_stats:
            vpp = stat.total_views / stat.post_count if stat.post_count > 0 else 0
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
        published = db.scalars(
            select(PublishedContentDB).where(PublishedContentDB.user_id == user_id)
        ).all()

        niches = db.scalars(
            select(MonitoredNiche).where(
                MonitoredNiche.user_id == user_id, MonitoredNiche.is_active
            )
        ).all()

        nodes = []
        links = []

        nodes.append({"id": "root", "group": 1, "label": "Empire Core"})

        niche_index = 1
        for niche in niches[:5]:
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

        content_index = 1
        for content in published[:10]:
            content_id = f"content_{content_index}"
            platform = content.platform if hasattr(content, "platform") else "Unknown"
            nodes.append(
                {"id": content_id, "group": 3, "label": f"{platform}_{content.id[:8]}"}
            )
            target = f"strat_{content_index}" if content_index < niche_index else "root"
            links.append({"source": target, "target": content_id, "value": 5})
            content_index += 1

        if len(nodes) <= 1:
            gateway_host = getattr(settings, "GATEWAY_HOST", "localhost")
            nodes.append(
                {
                    "id": "gateway_1",
                    "group": 1,
                    "label": gateway_host,
                    "status": "ONLINE",
                }
            )
            links.append({"source": "root", "target": "gateway_1", "value": 20})

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
        try:
            winning_tests = db.scalars(
                select(ABTestDB)
                .where(ABTestDB.winner_variant.isnot(None))
                .order_by(ABTestDB.created_at.desc())
                .limit(10)
            ).all()
        except Exception as e:
            logging.warning(f"[Empire] A/B test query failed: {e}")
            winning_tests = []

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

        if len(blueprints) < 5:
            try:
                top_posts = db.scalars(
                    select(PublishedContentDB)
                    .where(PublishedContentDB.user_id == user_id)
                    .order_by(PublishedContentDB.view_count.desc())
                    .limit(5)
                ).all()

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
            except Exception as e:
                logging.warning(f"[Empire] Fallback content query failed: {e}")

        return blueprints[:10]

    async def clone_strategy(
        self,
        db: Session,
        user_id: str,
        source_niche: str,
        target_niche: str,
        auto_publish: bool = False,
    ) -> bool:
        logging.info(
            f"[Empire] User {user_id} cloning strategy: {source_niche} -> {target_niche}"
        )

        try:
            source_monitored = db.scalars(
                select(MonitoredNiche).where(
                    MonitoredNiche.user_id == user_id,
                    MonitoredNiche.niche == source_niche,
                )
            ).first()

            if not source_monitored:
                logging.warning(
                    f"[Empire] Source niche '{source_niche}' not monitored by user {user_id}"
                )
                return False

            target_monitored = db.scalars(
                select(MonitoredNiche).where(
                    MonitoredNiche.user_id == user_id,
                    MonitoredNiche.niche == target_niche,
                )
            ).first()

            if not target_monitored:
                target_monitored = MonitoredNiche(
                    user_id=user_id, niche=target_niche, is_active=True
                )
                db.add(target_monitored)
            else:
                target_monitored.is_active = True

            existing_links = db.scalars(
                select(AffiliateLinkDB).where(
                    AffiliateLinkDB.user_id == user_id,
                    AffiliateLinkDB.niche == source_niche,
                )
            ).all()

            for link in existing_links:
                existing_target_link = db.scalars(
                    select(AffiliateLinkDB).where(
                        AffiliateLinkDB.user_id == user_id,
                        AffiliateLinkDB.niche == target_niche,
                        AffiliateLinkDB.product_name == link.product_name,
                        AffiliateLinkDB.link == link.link,
                    )
                ).first()

                if not existing_target_link:
                    new_link = AffiliateLinkDB(
                        user_id=user_id,
                        niche=target_niche,
                        product_name=link.product_name,
                        link=link.link,
                        cta_text=link.cta_text,
                    )
                    db.add(new_link)

            niche_setting_prefix = f"niche:{source_niche}:"
            source_settings = db.scalars(
                select(UserSetting).where(
                    UserSetting.user_id == user_id,
                    UserSetting.key.like(f"{niche_setting_prefix}%"),
                )
            ).all()

            for setting in source_settings:
                new_key = setting.key.replace(
                    f"niche:{source_niche}:", f"niche:{target_niche}:"
                )
                existing_target_setting = db.scalars(
                    select(UserSetting).where(
                        UserSetting.user_id == user_id, UserSetting.key == new_key
                    )
                ).first()

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
            logging.exception(f"[Empire] Clone strategy failed: {e}")
            return False

    async def get_activity_stream(
        self, db: Session, user_id: str
    ) -> list[dict[str, Any]]:
        events = []

        try:
            recent_posts = db.scalars(
                select(PublishedContentDB)
                .where(PublishedContentDB.user_id == user_id)
                .order_by(PublishedContentDB.published_at.desc())
                .limit(10)
            ).all()
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
        except Exception as e:
            logging.warning(f"[Empire] Publications query failed: {e}")

        try:
            recent_rev = db.scalars(
                select(RevenueLogDB)
                .where(RevenueLogDB.user_id == user_id)
                .order_by(RevenueLogDB.date.desc())
                .limit(5)
            ).all()
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
        except Exception as e:
            logging.warning(f"[Empire] Revenue query failed: {e}")

        try:
            recent_links = db.scalars(
                select(AffiliateLinkDB)
                .where(AffiliateLinkDB.user_id == user_id)
                .order_by(AffiliateLinkDB.created_at.desc())
                .limit(5)
            ).all()
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
        except Exception as e:
            logging.warning(f"[Empire] Affiliate links query failed: {e}")

        try:
            sentinel_logs = db.scalars(
                select(SystemActivityDB)
                .where(SystemActivityDB.module == "SENTINEL")
                .order_by(SystemActivityDB.created_at.desc())
                .limit(5)
            ).all()
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
        except Exception as e:
            logging.warning(f"[Empire] Sentinel query failed: {e}")

        events.sort(key=lambda x: x["timestamp"], reverse=True)
        return events[:15]


base_empire_service = EmpireService()
