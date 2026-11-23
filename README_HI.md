# Shree Karni QR Print System – Updated Starter

## फीचर्स
- Customer Photo/PDF Upload (25 MB)
- Automatic Amount: A4 ₹10, 4×6 Photo Sheet (8 photos) ₹40, ID Card ₹50, PVC ₹50
- Photo Rotate, Fit/Crop, White Background, 4×6 8-photo sheet
- PDF Preview, page range selection, rotation and crop margin
- Admin login, order search/filter, payment verification, status update, print/download
- QR code at `/qr.png` and health endpoint at `/health`

## Render Environment
Set `ADMIN_USER`, `ADMIN_PASSWORD`, `SECRET_KEY`, and `UPI_ID` in Render Environment.
Do not share secret values or screenshots showing them.

## Important storage warning
This starter uses SQLite and a local `uploads` folder. Render Free web services have ephemeral local filesystems; orders and uploads can be lost on restart/redeploy. For real shop use, attach a supported persistent disk (if available on your plan) and set `DATA_DIR` to its mount path, or migrate to managed PostgreSQL plus durable object storage before accepting real customer documents.

## Deploy
1. Back up your current GitHub repository and Render Environment first.
2. Replace the matching files from this ZIP in the existing repository. Keep your current secret values in Render Environment; do not commit them.
3. Commit to `main`; Render auto-deploys.
4. Test with a sample image and a sample PDF before using customer files.
5. Confirm Admin can open/print the uploaded files.

## Notes
- The 4×6 Photo Sheet creates an 8-photo layout from one selected image. Layout dimensions are a practical print sheet preview and may need printer-specific margin calibration.
- The PDF crop option crops equal margins from each selected page; test with copies first.
- Payment verification is a manual admin flag, not automatic bank/UPI confirmation.
- The current amount calculation is server-side; customer-submitted amount is ignored.
