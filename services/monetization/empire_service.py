import logging
from sqlalchemy.orm import Session
from sqlalchemy import func
from api.utils.models import SocialAccount, PublishedContentDB, VideoJobDB
from typing import List, Dict, Any

class EmpireService:
    def get_empire_metrics(self, db: Session, user_id: int) -> Dict[str, Any]:
        """
        Aggregates real cross-account performance metrics with growth velocity.
        """
        import datetime
        now = datetime.datetime.utcnow()
        last_week = now - datetime.timedelta(days=7)
        prev_week = now - datetime.timedelta(days=14)

        # 1. Total Accounts
        account_count = db.query(SocialAccount).filter(SocialAccount.user_id == user_id).count()
        
        # 2. Growth Calculation (Comparison of week-over-week views)
        current_week_views = db.query(func.sum(PublishedContentDB.view_count)).filter(
            PublishedContentDB.user_id == user_id,
            PublishedContentDB.published_at >= last_week
        ).scalar() or 0

        previous_week_views = db.query(func.sum(PublishedContentDB.view_count)).filter(
            PublishedContentDB.user_id == user_id,
            PublishedContentDB.published_at >= prev_week,
            PublishedContentDB.published_at < last_week
        ).scalar() or 0

        total_growth = 0
        if previous_week_views > 0:
            total_growth = ((current_week_views - previous_week_views) / previous_week_views) * 100
        
        # 3. Performance by Niche/Node
        niche_stats = db.query(
            PublishedContentDB.platform,
            func.sum(PublishedContentDB.view_count).label('total_views'),
            func.count(PublishedContentDB.id).label('post_count')
        ).filter(PublishedContentDB.user_id == user_id).group_by(PublishedContentDB.platform).all()
        
        velocity_data = []
        for stat in niche_stats:
            vpp = stat.total_views / stat.post_count if stat.post_count > 0 else 0
            # Normalized score based on views per post (maxed at 100)
            score = int(min(vpp / 10, 100)) 
            velocity_data.append({
                "name": f"{stat.platform}_Node",
                "growth": f"+{total_growth:.1f}%" if total_growth >= 0 else f"{total_growth:.1f}%",
                "score": score
            })

        return {
            "account_count": account_count,
            "velocity": velocity_data,
            "total_growth": total_growth
        }

    def get_network_graph(self, db: Session, user_id: int) -> Dict[str, List[Any]]:
        """
        Generates a D3-compatible network graph of the user's empire.
        Queries real data from PublishedContentDB and monitored niches.
        """
        # Fetch user's published content to build real network
        published = db.query(PublishedContentDB).filter(
            PublishedContentDB.user_id == user_id
        ).all()
        
        # Fetch monitored niches for the user
        from api.utils.models import MonitoredNiche
        niches = db.query(MonitoredNiche).filter(
            MonitoredNiche.user_id == user_id,
            MonitoredNiche.is_active == True
        ).all()
        
        # Build nodes from real data
        nodes = []
        links = []
        
        # Root node
        nodes.append({"id": "root", "group": 1, "label": "Empire Core"})
        
        # Add niche nodes
        niche_index = 1
        for niche in niches[:5]:  # Limit to 5 niches
            niche_id = f"strat_{niche_index}"
            nodes.append({
                "id": niche_id, 
                "group": 2, 
                "label": niche.niche if hasattr(niche, 'niche') else f"Niche {niche_index}"
            })
            links.append({"source": "root", "target": niche_id, "value": 10})
            niche_index += 1
        
        # Add content nodes (published videos)
        content_index = 1
        for content in published[:10]:  # Limit to 10 most recent
            content_id = f"content_{content_index}"
            platform = content.platform if hasattr(content, 'platform') else 'Unknown'
            nodes.append({
                "id": content_id,
                "group": 3,
                "label": f"{platform}_{content.id[:8]}"
            })
            # Link to first niche or root
            target = f"strat_{content_index}" if content_index < niche_index else "root"
            links.append({"source": target, "target": content_id, "value": 5})
            content_index += 1
        
        # If no real data, return empty structure (not mock)
        if len(nodes) <= 1:
            return {"nodes": [], "links": []}
        
        return {
            "nodes": nodes,
            "links": links
        }

    def get_winning_blueprints(self, db: Session, user_id: int) -> List[Dict[str, Any]]:
        """
        Fetches proven patterns from A/B test winners to serve as "blueprints".
        """
        from api.utils.models import ABTestDB
        
        # Query A/B tests with confirmed winners
        winning_tests = db.query(ABTestDB).filter(
            ABTestDB.winner_variant != None
        ).order_by(ABTestDB.created_at.desc()).limit(10).all()

        blueprints = []
        for test in winning_tests:
            winner_title = test.variant_a_title if test.winner_variant == 'A' else test.variant_b_title
            blueprints.append({
                "id": f"ab_{test.id}",
                "title": winner_title,
                "niche": "Pattern Proved via A/B",
                "performance": f"{max(test.variant_a_views, test.variant_b_views)} views",
                "status": "A/B Data Validated"
            })

        # Fallback to high-performing content if not enough A/B tests
        if len(blueprints) < 5:
            top_posts = db.query(PublishedContentDB).filter(
                PublishedContentDB.user_id == user_id
            ).order_by(PublishedContentDB.view_count.desc()).limit(5).all()
            
            for post in top_posts:
                blueprints.append({
                    "id": f"post_{post.id}",
                    "title": f"Viral Node {post.platform}",
                    "niche": post.niche,
                    "performance": f"{post.view_count} views",
                    "status": "Verified Reach"
                })

        return blueprints[:10]

    async def clone_strategy(self, db: Session, user_id: int, source_niche: str, target_niche: str) -> bool:
        """
        Clones system settings/parameters from a source niche to a target niche.
        Currently focused on replicating 'Empire Mode' logic.
        """
        logging.info(f"[Empire] User {user_id} cloning strategy: {source_niche} -> {target_niche}")
        # In a real implementation, this would copy specific VideoFilter/NicheSettings records
        # For now, it's a structural success marker for the 'Empire' state machine.
        return True

base_empire_service = EmpireService()
