(() => {
const fileInput = document.getElementById('file');
const preview = document.getElementById('preview');
const photoTools = document.getElementById('photoTools');
const pdfTools = document.getElementById('pdfTools');
const canvas = document.getElementById('photoCanvas');
const ctx = canvas.getContext('2d');
const printSize = document.getElementById('printSize');
const copies = document.getElementById('copies');
const amount = document.getElementById('amount');
const rates = {'A4':10,'4×6 Inch':40,'ID Card':50,'PVC Card 98×54 mm':50};
let image = null, rotation = 0, white = false, originalFile = null, pdfUrl = null;

function updateAmount(){const rate=rates[printSize.value]||10;const count=Math.max(1,Math.min(100,Number(copies.value)||1));amount.textContent='₹'+(rate*count).toFixed(2);}
printSize.addEventListener('change',updateAmount);copies.addEventListener('input',updateAmount);updateAmount();

function drawPhoto(){
 if(!image)return;
 const sheet=document.getElementById('makeSheet').checked && printSize.value==='4×6 Inch';
 if(sheet){
   canvas.width=1200;canvas.height=1800;ctx.fillStyle='white';ctx.fillRect(0,0,1200,1800);
   const w=500,h=390, gapX=70,gapY=35,startX=65,startY=70;
   for(let i=0;i<8;i++){const x=startX+(i%2)*(w+gapX),y=startY+Math.floor(i/2)*(h+gapY);drawOne(x,y,w,h);}
 }else{
   const max=1000, ratio=image.width/image.height;
   let w,h;if(ratio>=1){w=max;h=Math.round(max/ratio)}else{h=max;w=Math.round(max*ratio)}
   canvas.width=w;canvas.height=h;ctx.fillStyle=white?'white':'#f3f4f6';ctx.fillRect(0,0,w,h);drawOne(0,0,w,h);
 }
}
function drawOne(x,y,w,h){
 const fit=document.getElementById('photoFit').value;
 const iw=image.width,ih=image.height;let sx=0,sy=0,sw=iw,sh=ih;
 if(fit==='cover'){const target=w/h,src=iw/ih;if(src>target){sw=ih*target;sx=(iw-sw)/2}else{sh=iw/target;sy=(ih-sh)/2}}
 const off=document.createElement('canvas');off.width=w;off.height=h;const o=off.getContext('2d');
 o.fillStyle='white';o.fillRect(0,0,w,h);
 o.save();o.translate(w/2,h/2);o.rotate(rotation*Math.PI/180);
 const dw=(rotation%180===0)?w:h,dh=(rotation%180===0)?h:w;
 o.drawImage(image,sx,sy,sw,sh,-dw/2,-dh/2,dw,dh);o.restore();
 ctx.drawImage(off,x,y,w,h);
}
fileInput.addEventListener('change',()=>{
 const f=fileInput.files[0];originalFile=f;image=null;rotation=0;white=false;
 photoTools.classList.add('hidden');pdfTools.classList.add('hidden');preview.innerHTML='';
 if(!f){preview.textContent='फाइल चुनने पर Preview यहाँ दिखेगा';return;}
 if(f.type==='application/pdf'){
   pdfTools.classList.remove('hidden');if(pdfUrl)URL.revokeObjectURL(pdfUrl);pdfUrl=URL.createObjectURL(f);
   document.getElementById('pdfPreview').src=pdfUrl;preview.textContent='PDF चुनी गई: '+f.name;
 }else{
   photoTools.classList.remove('hidden');const img=document.createElement('img');img.src=URL.createObjectURL(f);img.alt='Photo preview';preview.appendChild(img);
   image=new Image();image.onload=drawPhoto;image.src=img.src;
 }
});
document.getElementById('rotateLeft').addEventListener('click',()=>{rotation=(rotation+270)%360;drawPhoto()});
document.getElementById('rotateRight').addEventListener('click',()=>{rotation=(rotation+90)%360;drawPhoto()});
document.getElementById('whiteBg').addEventListener('click',()=>{white=!white;drawPhoto()});
document.getElementById('photoFit').addEventListener('change',drawPhoto);
document.getElementById('makeSheet').addEventListener('change',drawPhoto);
printSize.addEventListener('change',drawPhoto);

document.getElementById('orderForm').addEventListener('submit',async(e)=>{
 const f=fileInput.files[0];if(!f)return;
 if(f.type!=='application/pdf' && image){
   e.preventDefault();
   drawPhoto();
   canvas.toBlob(blob=>{
     if(!blob){alert('Edited Photo तैयार नहीं हुई।');return;}
     const edited=new File([blob],printSize.value==='4×6 Inch'?'photo-sheet-8.jpg':'edited-photo.jpg',{type:'image/jpeg'});
     const dt=new DataTransfer();dt.items.add(edited);fileInput.files=dt.files;
     e.target.submit();
   },'image/jpeg',0.94);
 }else if(f.type==='application/pdf'){
   document.getElementById('pdfPagesHidden').value=document.getElementById('pdfPages').value;
   document.getElementById('pdfRotateHidden').value=document.getElementById('pdfRotate').value;
   document.getElementById('pdfCropHidden').value=document.getElementById('pdfCrop').value;
 }
});
})();