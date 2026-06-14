#!/bin/bash

# Configuration
SERVER="psalmprax@149.104.110.122"
REMOTE_DIR="/home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio"
LOCAL_OUT_DIR="./out"

echo "Syncing local changes to remote server..."
# Only sync the src directory to avoid overwriting node_modules
rsync -avz --exclude 'node_modules' --exclude 'out' ./src/ $SERVER:$REMOTE_DIR/src/

echo "Rendering CinematicLiquid..."
ssh $SERVER "cd $REMOTE_DIR && npx remotion render src/index.ts CinematicLiquid out/intro_CinematicLiquid.mp4"

echo "Rendering CinematicPrism..."
ssh $SERVER "cd $REMOTE_DIR && npx remotion render src/index.ts CinematicPrism out/intro_CinematicPrism.mp4"

echo "Rendering CinematicLidar..."
ssh $SERVER "cd $REMOTE_DIR && npx remotion render src/index.ts CinematicLidar out/intro_CinematicLidar.mp4"

echo "Rendering CinematicKinetic..."
ssh $SERVER "cd $REMOTE_DIR && npx remotion render src/index.ts CinematicKinetic out/intro_CinematicKinetic.mp4"

echo "Downloading rendered files..."
mkdir -p $LOCAL_OUT_DIR
scp $SERVER:$REMOTE_DIR/out/intro_CinematicLiquid.mp4 $LOCAL_OUT_DIR/
scp $SERVER:$REMOTE_DIR/out/intro_CinematicPrism.mp4 $LOCAL_OUT_DIR/
scp $SERVER:$REMOTE_DIR/out/intro_CinematicLidar.mp4 $LOCAL_OUT_DIR/
scp $SERVER:$REMOTE_DIR/out/intro_CinematicKinetic.mp4 $LOCAL_OUT_DIR/

echo "Done!"
