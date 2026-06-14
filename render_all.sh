#!/bin/bash
rsync -avz -e "ssh -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no" /home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/src/ root@149.104.110.122:/home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/src/

ssh -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no root@149.104.110.122 "cd /home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio && \
  npx remotion render src/index.ts CinematicIridescent out/intro_CinematicIridescent.mp4 --props='{\"title\":\"AURORA\", \"subtitle\":\"COLLECTION\", \"show_cta_overlay\":false}' --browser-executable /snap/bin/chromium --concurrency 1 --chromium-flags --no-sandbox --disable-setuid-sandbox --disable-gpu && \
  npx remotion render src/index.ts CinematicPortal out/intro_CinematicPortal.mp4 --props='{\"title\":\"ANCIENT\", \"subtitle\":\"MYSTERY\", \"show_cta_overlay\":false}' --browser-executable /snap/bin/chromium --concurrency 1 --chromium-flags --no-sandbox --disable-setuid-sandbox --disable-gpu && \
  npx remotion render src/index.ts CinematicCyberpunk out/intro_CinematicCyberpunk.mp4 --props='{\"title\":\"SYSTEM\", \"subtitle\":\"ONLINE\", \"show_cta_overlay\":false}' --browser-executable /snap/bin/chromium --concurrency 1 --chromium-flags --no-sandbox --disable-setuid-sandbox --disable-gpu"

scp -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no root@149.104.110.122:/home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out/intro_CinematicIridescent.mp4 /home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out/intro_CinematicIridescent.mp4
scp -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no root@149.104.110.122:/home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out/intro_CinematicPortal.mp4 /home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out/intro_CinematicPortal.mp4
scp -i /home/psalmprax/Music/id_rsa -o StrictHostKeyChecking=no root@149.104.110.122:/home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out/intro_CinematicCyberpunk.mp4 /home/psalmprax/ALL_PROJECTS/ettametta/apps/remotion-studio/out/intro_CinematicCyberpunk.mp4
