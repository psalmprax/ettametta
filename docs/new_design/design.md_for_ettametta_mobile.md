# Design System: Synthetic Intelligence OS (Ettametta Mobile)

## 1. Visual Direction
The design follows a "Synthetic Intelligence" aesthetic—a dark, high-contrast interface with neon accents that feels like a futuristic operating system. It prioritizes data density, motion-inspired visualizations, and a sleek, technical vibe suitable for AI-driven content creation and monitoring.

## 2. Core Styles
### Color Palette
- **Surface (Base):** `#131313` (Deep, matte black)
- **Primary Accent:** `#00FFFF` (Electric Cyan / Neon)
- **Secondary Accent:** `#A855F7` (Electric Purple)
- **Status/Success:** `#22C55E` (Vibrant Green)
- **Text (High Emphasis):** `#FFFFFF`
- **Text (Medium Emphasis):** `#94A3B8` (Slate-400)
- **Borders/Dividers:** `rgba(255, 255, 255, 0.1)`

### Typography
- **Primary Font:** Space Grotesk (Sans-serif, technical, monospace feel)
- **Headlines:** Large, bold, tracking-tighter for a "brutalist-tech" look.
- **Data Points:** Monospaced style for metrics to imply precision.

### Layout & Spacing
- **Grid:** Fluid 1-column layout for mobile.
- **Corners:** `4px` (Round Four) - maintaining a sharp, professional technical look rather than soft consumer-grade curves.
- **Blur Effects:** Heavy use of `backdrop-blur-xl` on top and bottom bars to create depth.

---

## 3. Screen-Specific Logic

### Screen 1: Viral Discovery (Dashboard)
- **Goal:** Real-time global signal monitoring.
- **Hero Element:** 3D Global Intelligence Visualization (The Globe).
- **Key Metrics:** High-glance cards for Scanning Speed, Active Nodes, and Signal Clarity.
- **Interactions:** "Test Drive" primary CTA with a lightning bolt icon, emphasizing speed and immediate action.

### Screen 2: Trending Signals (Feed)
- **Goal:** Content analysis and trend spotting.
- **Visual Hierarchy:** Large media thumbnails followed by "Viral Scores" and miniature sparkline charts.
- **Data Visualization:** Cyan wave charts indicating "Viral Velocity" to give immediate visual feedback on content momentum.
- **Status Tags:** High-contrast tags (e.g., `#NEURAL_NET`, `SYNCED`) to categorize high-velocity data.

### Screen 3: Creation Suite (Tools)
- **Goal:** Simplified AI content configuration.
- **Form Design:** Integrated dark-mode inputs with subtle cyan focus states.
- **Control Patterns:** High-contrast toggles (Cinema Mode) and stepped sliders for duration.
- **Feedback:** "System Ready" status indicator within the neural blueprint preview area.

---

## 4. Shared Components
- **TopAppBar:** Fixed, blurred background, featuring the Ettametta brand logo and user avatar.
- **BottomNavBar:** Persistent navigation with icon-based destinations: Explore, Signals/Generate, Create/Live, and Stats/Insights.
- **Action Buttons:** Large, full-width gradient buttons (`bg-cyan-400` to `bg-blue-500`) for primary "Launch" or "Generate" actions.
- **Metric Cards:** Semi-transparent black backgrounds with thin borders and glowing text for critical numbers.