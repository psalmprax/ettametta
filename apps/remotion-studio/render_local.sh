#!/bin/bash
echo "Rendering CinematicLiquid..."
npx remotion render src/index.ts CinematicLiquid out/intro_CinematicLiquid.mp4

echo "Rendering CinematicPrism..."
npx remotion render src/index.ts CinematicPrism out/intro_CinematicPrism.mp4

echo "Rendering CinematicLidar..."
npx remotion render src/index.ts CinematicLidar out/intro_CinematicLidar.mp4

echo "Rendering CinematicKinetic..."
npx remotion render src/index.ts CinematicKinetic out/intro_CinematicKinetic.mp4

echo "Done!"
