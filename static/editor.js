
(() => {
"use strict";

const fileInput = document.getElementById("file");
const preview = document.getElementById("preview");
const photoTools = document.getElementById("photoTools");
const pdfTools = document.getElementById("pdfTools");
const canvas = document.getElementById("photoCanvas");
const ctx = canvas.getContext("2d");

const printSize = document.getElementById("printSize");
const copies = document.getElementById("copies");
const amount = document.getElementById("amount");

const rates = {
    "A4": 10,
    "4×6 Inch": 40,
    "ID Card": 50,
    "PVC Card 98×54 mm": 50
};

let image = null;
let rotation = 0;
let white = false;
let pdfUrl = null;

function updateAmount() {
    const rate = rates[printSize.value] || 10;
    const count = Math.max(1, Math.min(100, Number(copies.value) || 1));
    amount.textContent = "₹" + (rate * count).toFixed(2);
}

function drawPhoto() {
    if (!image) return;

    const makeSheet =
        document.getElementById("makeSheet").checked &&
        printSize.value === "4×6 Inch";

    if (makeSheet) {
        canvas.width = 1200;
        canvas.height = 1800;

        ctx.fillStyle = "white";
        ctx.fillRect(0, 0, 1200, 1800);

        const w = 500;
        const h = 390;
        const gapX = 70;
        const gapY = 35;
        const startX = 65;
        const startY = 70;

        for (let i = 0; i < 8; i++) {
            const x = startX + (i % 2) * (w + gapX);
            const y = startY + Math.floor(i / 2) * (h + gapY);
            drawOne(x, y, w, h);
        }
    } else {
        const max = 1000;
        const ratio = image.width / image.height;

        let w, h;

        if (ratio >= 1) {
            w = max;
            h = Math.round(max / ratio);
        } else {
            h = max;
            w = Math.round(max * ratio);
        }

        canvas.width = w;
        canvas.height = h;

        ctx.fillStyle = white ? "white" : "#f3f4f6";
        ctx.fillRect(0, 0, w, h);

        drawOne(0, 0, w, h);
    }
}

function drawOne(x, y, w, h) {
    const fit = document.getElementById("photoFit").value;

    const iw = image.width;
    const ih = image.height;

    let sx = 0;
    let sy = 0;
    let sw = iw;
    let sh = ih;

    if (fit === "cover") {
        const target = w / h;
        const source = iw / ih;

        if (source > target) {
            sw = ih * target;
            sx = (iw - sw) / 2;
        } else {
            sh = iw / target;
            sy = (ih - sh) / 2;
        }
    }

    const off = document.createElement("canvas");
    off.width = w;
    off.height = h;

    const o = off.getContext("2d");

    o.fillStyle = "white";
    o.fillRect(0, 0, w, h);

    o.save();
    o.translate(w / 2, h / 2);
    o.rotate(rotation * Math.PI / 180);

    const dw = rotation % 180 === 0 ? w : h;
    const dh = rotation % 180 === 0 ? h : w;

    o.drawImage(
        image,
        sx, sy, sw, sh,
        -dw / 2, -dh / 2, dw, dh
    );

    o.restore();
    ctx.drawImage(off, x, y, w, h);
}

// FILE SELECTION
fileInput.addEventListener("change", () => {
    const f = fileInput.files[0];

    image = null;
    rotation = 0;
    white = false;

    photoTools.classList.add("hidden");
    pdfTools.classList.add("hidden");

    preview.innerHTML = "";

    if (!f) {
        preview.textContent = "फाइल चुनने पर Preview यहाँ दिखेगा";
        return;
    }

    if (f.type === "application/pdf") {
        pdfTools.classList.remove("hidden");

        if (pdfUrl) URL.revokeObjectURL(pdfUrl);

        pdfUrl = URL.createObjectURL(f);

        document.getElementById("pdfPreview").src = pdfUrl;

        preview.textContent = "PDF चुनी गई: " + f.name;

        document.getElementById("pageStart").value = 1;
        document.getElementById("pageEnd").value = "";

    } else {
        photoTools.classList.remove("hidden");

        const imgUrl = URL.createObjectURL(f);

        const img = document.createElement("img");
        img.src = imgUrl;
        img.alt = "Photo Preview";

        preview.appendChild(img);

        image = new Image();

        image.onload = drawPhoto;
        image.onerror = () => alert("फोटो Preview नहीं खुल पाया।");

        image.src = imgUrl;
    }
});

// PHOTO CONTROLS
document.getElementById("rotateLeft").addEventListener("click", () => {
    rotation = (rotation + 270) % 360;
    drawPhoto();
});

document.getElementById("rotateRight").addEventListener("click", () => {
    rotation = (rotation + 90) % 360;
    drawPhoto();
});

document.getElementById("whiteBg").addEventListener("click", () => {
    white = !white;
    drawPhoto();
});

document.getElementById("photoFit").addEventListener("change", drawPhoto);
document.getElementById("makeSheet").addEventListener("change", drawPhoto);

printSize.addEventListener("change", () => {
    updateAmount();
    drawPhoto();
});

copies.addEventListener("input", updateAmount);

// FORM SUBMIT
document.getElementById("orderForm").addEventListener("submit", (e) => {
    const f = fileInput.files[0];

    if (!f) return;

    if (f.type === "application/pdf") {

        const start = Number(document.getElementById("pageStart").value);
        const endText = document.getElementById("pageEnd").value.trim();
        const end = endText === "" ? "" : Number(endText);

        if (!Number.isInteger(start) || start < 1) {
            e.preventDefault();
            alert("Starting Page सही भरें।");
            return;
        }

        if (end !== "" && (!Number.isInteger(end) || end < start)) {
            e.preventDefault();
            alert("Ending Page सही भरें।");
            return;
        }

        document.getElementById("pdfRotateHidden").value =
            document.getElementById("pdfRotate").value;

        document.getElementById("pdfCropHidden").value =
            document.getElementById("pdfCrop").value;

        return;
    }

    if (image) {
        e.preventDefault();

        drawPhoto();

        canvas.toBlob((blob) => {
            if (!blob) {
                alert("Edited Photo तैयार नहीं हुई।");
                return;
            }

            const edited = new File(
                [blob],
                printSize.value === "4×6 Inch"
                    ? "photo-sheet-8.jpg"
                    : "edited-photo.jpg",
                { type: "image/jpeg" }
            );

            const dt = new DataTransfer();
            dt.items.add(edited);

            fileInput.files = dt.files;

            e.target.submit();

        }, "image/jpeg", 0.94);
    }
});

// INITIALIZE
updateAmount();

})();
