# Tool Preview Images Placeholder

PUT TOOL PREVIEW IMAGES HERE.

Expected files (referenced in src/components/ToolsMosaic.astro):

  public/tools/timelapse-preview.jpg
    → Preview image for the Timelapse Creator card
    → Recommended size: 800×500px (16:10 ratio)

  public/tools/baumportraets-preview.jpg
    → Preview image for the Baumarten­porträts card
    → Recommended size: 800×500px (16:10 ratio)

Once images are added, update each tool's `image` field in ToolsMosaic.astro:
  image: '/tools/timelapse-preview.jpg'
  image: '/tools/baumportraets-preview.jpg'
