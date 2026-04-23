#!/bin/bash
#
# Generate and Download Enhanced Videos
# ======================================
# Generates videos from all working models with upscale/enhancement
# and downloads them to local test_videos folder

set -e

# SSH Configuration
GPU_HOST="root@175.155.64.174"
GPU_PORT="19461"
SSH_KEY="/home/psalmprax/Music/id_rsa"
SSH_OPTS="-o StrictHostKeyChecking=no -o PasswordAuthentication=no"

# Local output
OUTPUT_DIR="/home/psalmprax/ALL_PROJECTS/ettametta/test_videos"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# GPU Server URL
GPU_URL="http://175.155.64.174:8080"

echo "=========================================="
echo "Generating Enhanced Videos from All Models"
echo "=========================================="

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Function to generate video and wait
generate_enhanced() {
    local model=$1
    local prompt=$2
    local output_name=$3
    
    echo ""
    echo ">>> Generating: $model"
    echo "    Prompt: $prompt"
    
    # Try the model's specific endpoint
    case $model in
        "cogvideo_5b")
            # Use cogvideo endpoint with upscale params
            curl -s -m 180 -X POST "${GPU_URL}/models/cogvideo_5b/generate" \
                -H "Content-Type: application/json" \
                -d "{\"prompt\": \"$prompt\", \"upscale_factor\": 4, \"enhance_face\": true, \"num_inference_steps\": 30, \"num_frames\": 49}" &
            ;;
        "hunyuan_480p")
            # Use hunyuan endpoint
            curl -s -m 180 -X POST "${GPU_URL}/generate_hunyuan" \
                -H "Content-Type: application/json" \
                -d "{\"prompt\": \"$prompt\", \"upscale\": true}" &
            ;;
        "ltx_2_19b")
            # Use main generate endpoint
            curl -s -m 180 -X POST "${GPU_URL}/generate" \
                -H "Content-Type: application/json" \
                -d "{\"prompt\": \"$prompt\", \"upscale_factor\": 4, \"enhance_face\": true}" &
            ;;
        "wan_2_1_t2v")
            # Use generate endpoint
            curl -s -m 180 -X POST "${GPU_URL}/generate" \
                -H "Content-Type: application/json" \
                -d "{\"prompt\": \"$prompt\", \"upscale_factor\": 4, \"enhance_face\": true}" &
            ;;
        "mochi")
            # Use generate endpoint
            curl -s -m 180 -X POST "${GPU_URL}/generate" \
                -H "Content-Type: application/json" \
                -d "{\"prompt\": \"$prompt\", \"upscale_factor\": 4}" &
            ;;
        *)
            echo "Unknown model: $model"
            ;;
    esac
    
    echo "    Submitted generation job for $model"
}

# Test prompts for each model
declare -A PROMPTS
PROMPTS["cogvideo_5b"]="A futuristic neon city at night with rain reflecting on surfaces, cinematic quality, 4k"
PROMPTS["hunyuan_480p"]="A serene mountain landscape with flowing river at sunset, golden hour lighting"
PROMPTS["ltx_2_19b"]="An animated character dancing smoothly in a modern studio, professional lighting"
PROMPTS["wan_2_1_t2v"]="A cosmic nebula with stars and galaxies in deep space, stunning visuals"
PROMPTS["mochi"]="A close-up of a flower blooming in beautiful time-lapse photography"

# Generate in parallel
echo ""
echo "Step 1: Submitting generation jobs..."

for model in cogvideo_5b hunyuan_480p ltx_2_19b wan_2_1_t2v mochi; do
    generate_enhanced "$model" "${PROMPTS[$model]}" "${model}_${TIMESTAMP}"
done

# Wait for generations to complete
echo ""
echo "Step 2: Waiting for video generation (90 seconds)..."
sleep 90

# Check what's available
echo ""
echo "Step 3: Checking generated videos..."
ssh $SSH_OPTS -i $SSH_KEY -p $GPU_PORT $GPU_HOST "ls -la /workspace/ai_content/" 2>/dev/null || echo "No videos found"

# Download all videos
echo ""
echo "Step 4: Downloading videos..."
scp $SSH_OPTS -i $SSH_KEY -P $GPU_PORT "$GPU_HOST:/workspace/ai_content/*.mp4" "$OUTPUT_DIR/" 2>/dev/null || echo "Download complete"

# List what we got
echo ""
echo "=========================================="
echo "Videos in $OUTPUT_DIR:"
ls -lh "$OUTPUT_DIR"
echo "=========================================="