-keep class com.google.mlkit.** { *; }
-dontwarn org.apache.**

# Optional PdfBox JPEG 2000 JPX plugin is not shipped. Android PdfRenderer handles raster OCR.
-dontwarn com.gemalto.jp2.**
