# Phase 02 Research: Content Discovery

**Researcher:** Kilo
**Date:** 2026-04-09
**Phase:** Content Discovery
**Goal:** Research how to implement Phase 2: Content Discovery - Users can discover and analyze trending content

## Executive Summary

Content discovery is the foundation for viral content creation. This phase requires building automated scanners for multiple social media platforms to collect trending content, implement search/filter capabilities, and add AI-powered analysis for viral patterns. Key challenges include API rate limits, data freshness, and computing viral scores that correlate with actual virality.

## Technical Approach

### Platform Integration Strategy

#### YouTube
- **API:** YouTube Data API v3 (Google APIs)
- **Trending:** `videos.list` with `chart=mostPopular` parameter
- **Search:** `search.list` with advanced filters
- **Rate Limits:** 10,000 units/day (free quota)
- **Data Points:** title, description, channel, views, likes, comments, publish date, duration, thumbnails

#### TikTok
- **API:** TikTok for Developers (Research API) - limited access, requires approval
- **Alternative:** Third-party scrapers or unofficial APIs (risky, terms violation)
- **Trending:** No direct trending endpoint; use search with popularity sort
- **Data Points:** video URL, creator, description, views, likes, shares, comments, hashtags

#### Other Platforms (Future)
- Instagram: Graph API (business accounts only)
- Facebook: Graph API
- Twitter/X: API v2
- Reddit: API (PRAW library)

**Recommendation:** Start with YouTube (reliable API), TikTok via approved Research API if possible, or implement controlled scraping with rate limiting.

### Data Architecture

#### Content Model
```sql
CREATE TABLE content (
    id UUID PRIMARY KEY,
    platform VARCHAR NOT NULL, -- 'youtube', 'tiktok', etc.
    external_id VARCHAR UNIQUE NOT NULL, -- platform's content ID
    title TEXT,
    description TEXT,
    creator_name VARCHAR,
    creator_id VARCHAR,
    url TEXT NOT NULL,
    thumbnail_url TEXT,
    duration_seconds INTEGER,
    view_count BIGINT DEFAULT 0,
    like_count BIGINT DEFAULT 0,
    comment_count BIGINT DEFAULT 0,
    share_count BIGINT DEFAULT 0,
    published_at TIMESTAMP,
    scanned_at TIMESTAMP DEFAULT NOW(),
    viral_score DECIMAL(5,2),
    tags TEXT[], -- hashtags, keywords
    metadata JSONB -- platform-specific data
);
```

#### Viral Score Calculation
```
viral_score = (
    0.4 * (views / age_hours) + 
    0.3 * engagement_rate + 
    0.2 * growth_velocity + 
    0.1 * recency_bonus
)
```

Where:
- engagement_rate = (likes + comments + shares) / views
- growth_velocity = views_last_24h / views_total
- recency_bonus = 1 / (1 + age_hours/24)

### Scanning Infrastructure

#### Scheduler
- Celery periodic tasks for trending scans
- Configurable intervals (every 1-4 hours)
- Platform-specific schedules (YouTube trending updates every 15min)

#### Error Handling
- API quota exceeded: exponential backoff
- Network failures: retry with jitter
- Invalid tokens: alert admin for refresh

#### Deduplication
- Check external_id before insert
- Update existing records if newer data available

### Search and Filtering

#### Search Implementation
- Full-text search on title + description + tags
- PostgreSQL tsvector for performance
- Filters: platform, date_range, min_views, min_viral_score, creator, hashtags

#### Sorting Options
- viral_score DESC (default)
- published_at DESC
- view_count DESC
- engagement_rate DESC

### AI Analysis for Viral Patterns

#### Pattern Recognition
- **Topic Modeling:** Use BERTopic or LDA to identify trending topics
- **Sentiment Analysis:** VADER or transformers for emotional tone
- **Viral Predictors:** ML model trained on historical viral content

#### Implementation
- Background Celery tasks for analysis
- Store analysis results in separate table
- Cache results for performance

#### Insights Generation
- "Top hashtags in trending content"
- "Average engagement by topic"
- "Viral score distribution"
- "Content length vs virality correlation"

### API Design

#### Endpoints
- `GET /api/content/trending` - Get trending content
- `GET /api/content/search` - Search with filters
- `GET /api/content/{id}/analysis` - Get AI analysis for content
- `POST /api/content/scan` - Manual trigger scan

#### Response Format
```json
{
  "id": "uuid",
  "platform": "youtube",
  "title": "Amazing Content",
  "url": "https://youtube.com/watch?v=...",
  "thumbnail_url": "https://...",
  "stats": {
    "views": 1000000,
    "likes": 50000,
    "viral_score": 85.2
  },
  "published_at": "2023-04-09T10:00:00Z",
  "analysis": {
    "topics": ["gaming", "esports"],
    "sentiment": "positive",
    "viral_potential": "high"
  }
}
```

### Security Considerations

#### API Keys Management
- Store platform API keys in environment variables
- Rotate keys periodically
- Monitor usage to avoid quota exhaustion

#### Content Moderation
- Filter out inappropriate content
- Respect platform content policies
- Implement user reporting system

### Performance Optimization

#### Caching Strategy
- Redis cache for trending content (TTL: 1 hour)
- Cache search results (TTL: 30 min)
- Cache analysis results (TTL: 24 hours)

#### Database Indexing
- Indexes on: platform, published_at, viral_score, view_count
- GIN index on tags array
- Full-text search index

### Integration Points

#### Phase 1 Dependencies
- User authentication for personalized content
- User preferences for content filtering

#### Phase 3 Handover
- Selected content passed to video generation
- Content metadata used for AI prompts

### Validation Architecture

#### Nyquist Validation Dimensions

**Dimension 1: Functional Correctness**
- Automated scanners retrieve content from platforms
- Content data is accurately stored and retrievable
- Search filters work correctly
- Viral scores calculate properly

**Dimension 2: Data Quality**
- Content freshness (within 4 hours of trending)
- Complete metadata collection
- No duplicate content entries
- Accurate engagement metrics

**Dimension 3: Performance**
- Trending endpoint responds < 200ms
- Search queries complete < 500ms
- Scanner runs don't exceed 30 minutes
- Background analysis completes within 5 minutes per content

**Dimension 4: Reliability**
- 99.9% uptime for content access
- Graceful handling of API failures
- Automatic retry mechanisms
- Alert system for quota issues

**Dimension 5: Security**
- API keys properly secured
- No unauthorized access to content data
- Content moderation filters active
- User data privacy maintained

**Dimension 6: User Experience**
- Intuitive search interface
- Fast loading of content lists
- Clear viral score indicators
- Helpful analysis insights

**Dimension 7: Scalability**
- Handles 1000+ trending items per platform
- Supports multiple concurrent users
- Database queries scale with data growth
- Background tasks don't overwhelm system

**Dimension 8: Validation Strategy**
- Unit tests for viral score calculations
- Integration tests for API endpoints
- End-to-end tests for full discovery flow
- Performance tests for search and trending
- Mock external APIs for testing

### Implementation Risks

#### High Risk
- TikTok API access (may require special approval)
- API rate limits causing data gaps
- Viral score formula not correlating with actual virality

#### Medium Risk
- Content analysis accuracy
- Database performance with large content volumes
- Platform API changes breaking integration

#### Mitigation Strategies
- Implement multiple data sources for TikTok
- Monitor API usage and implement intelligent caching
- A/B test viral score formulas with user feedback
- Use database partitioning for scalability
- Implement API versioning and monitoring

### Success Metrics

- **Coverage:** Trending content from 3+ platforms
- **Freshness:** Content updated within 2 hours
- **Accuracy:** 95%+ viral score correlation with manual assessment
- **Performance:** Search results in < 300ms
- **Reliability:** 99.5% scanner success rate

## Conclusion

Content discovery requires robust platform integrations, efficient data storage, and intelligent analysis. Focus on YouTube first for reliable API access, implement comprehensive viral scoring, and build extensible architecture for additional platforms. AI analysis will differentiate this system from basic aggregators.</content>
<parameter name="filePath">.planning/phases/02-content-discovery/02-RESEARCH.md