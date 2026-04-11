# Admin UI vs System Parameters Configuration Guide

## Overview

This guide categorizes all configuration parameters into two groups:
1. **Admin UI Configurable** - Parameters that can be set through the admin interface
2. **System Parameters** - Parameters that must be set at deployment/environment level

## 1. Admin UI Configurable Parameters

These parameters can be safely configured through the admin UI without affecting deployment:

### API Keys & External Services
- **LLM Providers**: groq_api_key, openai_api_key, anthropic_api_key, xai_api_key, deepseek_api_key, google_api_key, cohere_api_key, mistral_api_key, cerebras_api_key, cloudflare_api_key, hugging_face_api_key, openrouter_api_key, nvidia_api_key, ollama_cloud_api_key, siliconflow_api_key
- **Social Media**: youtube_api_key, tiktok_api_key, tiktok_client_key, tiktok_client_secret, google_client_id, google_client_secret
- **Payment**: stripe_secret_key
- **E-commerce**: shopify_access_token, shopify_shop_url, printful_api_key
- **Communication**: telegram_bot_token, telegram_admin_id, twilio_account_sid, twilio_auth_token, twilio_whatsapp_number
- **Email Marketing**: mailchimp_api_key, mailchimp_list_id, convertkit_api_key
- **Affiliate**: amazon_associates_tag, amazon_paapi_key, amazon_paapi_tag, impact_radius_api_key, shareasale_api_key
- **Trading**: alpha_vantage_api_key, coingecko_api_key
- **Video/Voice**: elevenlabs_api_key, fish_speech_endpoint, pexels_api_key, google_search_cx, runway_api_key, pika_api_key, zsky_api_key, kling_api_key, pixverse_api_key, replicate_api_key, stability_api_key

### Feature Toggles & Business Logic
- **LLM Settings**: default_llm_provider, use_os_models, default_vlm_model
- **Video Generation**: ai_video_provider, ai_video_fallbacks, default_quality_tier
- **Audio/Visual**: voice_engine, enable_sound_design, enable_motion_graphics, music_volume, sfx_volume
- **Advanced Features**: enable_langchain, enable_crewai, enable_interpreter, enable_affiliate_api, enable_trading, enable_opencli
- **Rate Limiting**: limit_free, limit_pro, limit_sovereign, gpu_queue_slots, gpu_queue_timeout
- **Monetization**: monetization_mode

### URLs & Endpoints (Admin Configurable)
- **External URLs**: production_domain, cors_origins, render_node_url
- **Local Services**: ollama_url, lm_studio_url, comfyui_url

## 2. System Parameters (Deployment-Level Only)

These parameters must be set via environment variables or deployment configuration:

### Security & Authentication
- **SECRET_KEY**: JWT signing key (32+ characters required in production)
- **INTERNAL_API_TOKEN**: Token for service-to-service communication
- **STRIPE_WEBHOOK_SECRET**: Stripe webhook signature verification
- **Webhook Secrets**: youtube_webhook_secret, tiktok_webhook_secret, instagram_webhook_secret, facebook_webhook_secret, linkedin_webhook_secret, x_webhook_secret

### Infrastructure & Architecture
- **APP_NAME**: Application identifier
- **ENV**: Environment (development/production)
- **DEBUG**: Debug mode flag
- **PORT**: API server port
- **API_URL**: Internal service URL for inter-service communication
- **DATABASE_URL**: Database connection string
- **REDIS_URL**: Redis connection URL
- **STORAGE_* Settings**: Cloud storage configuration (provider, endpoint, access keys, etc.)
- **ALGORITHM**: JWT algorithm (fixed as HS256)

### File System & Paths
- **FONT_PATH**: System font path
- **SOUND_LIBRARY_PATH**: Audio library directory
- **COMFYUI_WORKFLOWS_DIR**: ComfyUI workflows directory
- **COMFYUI_MODELS_DIR**: ComfyUI models directory
- **OPENCLI_BIN**: Path to opencli binary
- **OPENCLI_SESSIONS_DIR**: OpenCLI session storage directory
- **YOUTUBE_COOKIES_PATH**: YouTube cookies file path
- **TIKTOK_COOKIES_PATH**: TikTok cookies file path

### Core Application Settings
- **CLEANUP_TRANSIENT_MODELS**: Model cleanup behavior
- **GPU_QUEUE_SLOTS**: Concurrent GPU operations
- **GPU_QUEUE_TIMEOUT**: GPU operation timeout

## Migration Strategy

### Current State
- All parameters are in `api/config.py` with defaults
- Environment variables override defaults
- Some parameters are exposed in admin UI through `api/routes/settings.py`

### Recommended Migration

1. **Move Admin UI parameters to database**:
   ```sql
   -- SystemSettings table already exists
   -- Populate with current environment values
   ```

2. **Keep System parameters in environment**:
   - Update `.env.example` with only system parameters
   - Document required vs optional system parameters

3. **Update configuration loading**:
   - Admin UI parameters: Load from database with environment fallback
   - System parameters: Environment only (no database fallback)

## Example .env File (Production)

```bash
# System Parameters Only
SECRET_KEY=your_32_char_secret_key_here
ENV=production
DEBUG=false
PORT=8000
DATABASE_URL=postgresql://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
API_URL=http://api:8000
STORAGE_PROVIDER=AWS
STORAGE_ACCESS_KEY=your_aws_key
STORAGE_SECRET_KEY=your_aws_secret
STORAGE_BUCKET=your_bucket
STORAGE_REGION=us-east-1

# Optional System Parameters
INTERNAL_API_TOKEN=your_service_token
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret
COMFYUI_WORKFLOWS_DIR=/path/to/workflows
COMFYUI_MODELS_DIR=/path/to/models
```

## Admin UI Settings Categories

The admin UI should organize settings into these categories:

1. **LLM Configuration**
   - Default provider selection
   - API key management
   - Model settings

2. **Social Media & OAuth**
   - Platform API keys
   - OAuth credentials

3. **Payment & Monetization**
   - Payment processors
   - Monetization settings

4. **Video & Audio**
   - Video generation providers
   - Audio settings

5. **E-commerce & Marketing**
   - Store integrations
   - Email marketing
   - Affiliate programs

6. **Advanced Features**
   - Feature toggles
   - Rate limits
   - URLs and endpoints

## Security Considerations

- **Never store sensitive system parameters in database**
- **API keys in database should be encrypted** (SystemSettings table supports encrypted values)
- **System parameters must be validated on startup** (see `validate_critical_config()`)
- **Admin UI should mask sensitive values** in logs and responses

## Implementation Notes

- Use the existing `get_secret()` function for hierarchical lookup
- System parameters bypass database lookup for security
- Admin UI parameters use database with environment fallback
- Add validation for system parameters on application startup</content>
<parameter name="filePath">/home/psalmprax/ALL_PROJECTS/viral_forge/docs/admin_ui_vs_system_parameters.md