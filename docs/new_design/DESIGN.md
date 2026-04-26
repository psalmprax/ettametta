---
name: Synthetic Intelligence OS
colors:
  surface: '#131313'
  surface-dim: '#131313'
  surface-bright: '#393939'
  surface-container-lowest: '#0e0e0e'
  surface-container-low: '#1c1b1b'
  surface-container: '#201f1f'
  surface-container-high: '#2a2a2a'
  surface-container-highest: '#353534'
  on-surface: '#e5e2e1'
  on-surface-variant: '#b9cac9'
  inverse-surface: '#e5e2e1'
  inverse-on-surface: '#313030'
  outline: '#839493'
  outline-variant: '#3a4a49'
  surface-tint: '#00dddd'
  primary: '#ffffff'
  on-primary: '#003737'
  primary-container: '#00fbfb'
  on-primary-container: '#007070'
  inverse-primary: '#006a6a'
  secondary: '#ecb1ff'
  on-secondary: '#520070'
  secondary-container: '#d05bff'
  on-secondary-container: '#480063'
  tertiary: '#ffffff'
  on-tertiary: '#053900'
  tertiary-container: '#79ff5b'
  on-tertiary-container: '#117500'
  error: '#ffb4ab'
  on-error: '#690005'
  error-container: '#93000a'
  on-error-container: '#ffdad6'
  primary-fixed: '#00fbfb'
  primary-fixed-dim: '#00dddd'
  on-primary-fixed: '#002020'
  on-primary-fixed-variant: '#004f4f'
  secondary-fixed: '#f9d8ff'
  secondary-fixed-dim: '#ecb1ff'
  on-secondary-fixed: '#320046'
  on-secondary-fixed-variant: '#75009e'
  tertiary-fixed: '#79ff5b'
  tertiary-fixed-dim: '#2ae500'
  on-tertiary-fixed: '#022100'
  on-tertiary-fixed-variant: '#095300'
  background: '#131313'
  on-background: '#e5e2e1'
  surface-variant: '#353534'
typography:
  display-lg:
    fontFamily: Space Grotesk
    fontSize: 40px
    fontWeight: '700'
    lineHeight: '1.1'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Space Grotesk
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.2'
  body-base:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.5'
  data-mono:
    fontFamily: Space Grotesk
    fontSize: 14px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.05em
  label-caps:
    fontFamily: Space Grotesk
    fontSize: 12px
    fontWeight: '700'
    lineHeight: '1.2'
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 4px
  xs: 4px
  sm: 8px
  md: 16px
  lg: 24px
  xl: 40px
  container-margin: 20px
  gutter: 12px
---

## Brand & Style

The design system is engineered to feel like a high-performance terminal for the next generation of creators. It adopts a **Glassmorphic-Futurist** aesthetic, prioritizing data density and tactical precision. The UI evokes the feeling of a sophisticated Operating System rather than a standard mobile app, utilizing depth and light to guide the user through complex AI workflows.

The personality is authoritative and powerful, characterized by pitch-black voids contrasted against vibrant, emissive light sources. This system targets power users who require high-fidelity analytics and seamless AI generation tools, providing an environment that feels both cutting-edge and professional.

## Colors

The color palette is built on a foundation of absolute black (#000000) to ensure maximum contrast and energy efficiency on OLED displays. 

- **Electric Cyan (#00FFFF)** acts as the primary signal color for creation and affirmative actions.
- **Vibrant Purple (#BF00FF)** is used for intelligence-driven features and secondary hierarchy.
- **Neon Green (#39FF14)** is reserved strictly for positive growth metrics and "active" system states.
- **Surface Neutrals** are achieved through low-opacity whites (3-8%) layered over the black background to create a sense of depth without losing the "pitch black" essence.

## Typography

This design system utilizes a dual-font strategy to balance legibility with a technical aesthetic. 

**Space Grotesk** is the primary typeface for headlines, data points, and UI labels. Its geometric, technical construction reinforces the "OS" personality and provides a futuristic rhythm for analytical content. 

**Inter** is used for all long-form body text and descriptions. Its neutral, systematic nature ensures that complex AI-generated insights remain readable at smaller scales. Use uppercase tracking for small labels to enhance the tactical, command-center appearance.

## Layout & Spacing

The system follows a strict **4px baseline grid** to ensure mathematical precision in all component alignments. For mobile layouts, a **4-column fluid grid** is used with a 20px margin. 

Layouts should prioritize "Information Density." Avoid excessive whitespace; instead, use thin borders and subtle tonal shifts to separate content areas. Elements should feel docked or slotted into a grid, emphasizing the systematic nature of the platform.

## Elevation & Depth

Depth is conveyed through **Glassmorphism** and light emission rather than traditional shadows. 

- **Base Layer:** Pure #000000.
- **Surface Layer:** Semi-transparent white overlay (3-5%) with a 20px background blur (backdrop-filter).
- **Rim Lighting:** Instead of drop shadows, use 1px inner borders with a 10-20% opacity of the primary accent color to suggest that the component is glowing from within.
- **Active State Elevation:** Components move "closer" to the user by increasing the opacity of the glass surface and the intensity of the rim light.

## Shapes

The design system uses a **Soft Tech** approach to shapes. Primary UI containers and buttons use a 0.25rem (4px) corner radius, creating a precision-milled look that is sharper and more professional than standard consumer apps. 

Data visualization nodes and specific status indicators may use 0px (sharp) corners to reinforce a "terminal" aesthetic. Interactive elements like toggle switches or floating action buttons may use pill-shaped (rounded-full) geometry to distinguish them from structural layout components.

## Components

- **Primary Buttons:** Utilize the `action-primary` gradient. Text is high-contrast black or white depending on the gradient's luminance. Buttons should have a slight "outer glow" shadow using the primary accent color at low opacity.
- **Glass Cards:** No solid background color. Use a 1px border (#FFFFFF at 10% opacity) and `surface-glass` fill.
- **Input Fields:** Bottom-border only or thin 4-sided borders. When focused, the border transitions to Electric Cyan with a subtle glow effect.
- **Data Visualizations:** High-contrast lines using Neon Green and Cyan. Charts should include a gradient fill from the stroke color to transparent.
- **Status Chips:** Small, rectangular shapes with 0px radius. Use Neon Green for "Live" or "Synced" states, and Electric Cyan for "Processing."
- **Navigation:** A bottom-docked translucent bar with icons that "activate" with a vertical accent line beneath them when selected.