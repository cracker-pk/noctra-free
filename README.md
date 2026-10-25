# NOCTRA Free

A static, responsive gallery of PC and mobile wallpapers. Each wallpaper has downloadable PC (3840×2160), tablet (3840×2560), and mobile (2160×3840) WebP variants.

The images are generated from the source files in `wallpaper-pc/` and `wallpaper-phone/` by `enhance_wallpapers.py`. The script crops to each target aspect ratio, enlarges with Lanczos resampling, applies restrained sharpening and color/contrast adjustments, and creates smaller gallery thumbnails. Upscaling increases pixel dimensions but cannot recreate detail missing from a lower-resolution source.

To rebuild the downloadable gallery files:

```powershell
python .\enhance_wallpapers.py
```

The GitHub Pages workflow publishes only the contents of `public/`.
