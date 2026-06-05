// 生成简单的托盘图标
// 运行: node generate-icon.js

const fs = require('fs');
const zlib = require('zlib');

// 创建一个简单的 32x32 蓝色背景 + 白色 "LC" 文字图标
function createIcon() {
  const width = 32;
  const height = 32;
  const channels = 3; // RGB

  // 创建像素数据
  const rawData = Buffer.alloc(width * height * channels);

  // 填充蓝色背景 (#4A90E2)
  for (let i = 0; i < width * height; i++) {
    rawData[i * 3] = 0x4A;     // R
    rawData[i * 3 + 1] = 0x90; // G
    rawData[i * 3 + 2] = 0xE2; // B
  }

  // 绘制简单的 "LC" 文字（白色像素）
  const drawPixel = (x, y) => {
    if (x >= 0 && x < width && y >= 0 && y < height) {
      const idx = (y * width + x) * 3;
      rawData[idx] = 255;
      rawData[idx + 1] = 255;
      rawData[idx + 2] = 255;
    }
  };

  // 绘制 "L" (左边)
  for (let y = 8; y < 24; y++) {
    drawPixel(8, y);
    drawPixel(9, y);
  }
  for (let x = 8; x < 14; x++) {
    drawPixel(x, 23);
  }

  // 绘制 "C" (右边)
  for (let y = 8; y < 24; y++) {
    drawPixel(18, y);
    drawPixel(19, y);
  }
  for (let x = 18; x < 26; x++) {
    drawPixel(x, 8);
    drawPixel(x, 9);
    drawPixel(x, 22);
    drawPixel(x, 23);
  }

  // 创建 PNG
  const png = createPng(rawData, width, height);
  fs.writeFileSync('tray-icon.png', png);
  console.log('✅ 图标已生成: tray-icon.png');
}

function createPng(rawData, width, height) {
  // PNG 签名
  const signature = Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]);

  // IHDR chunk
  const ihdrData = Buffer.alloc(13);
  ihdrData.writeUInt32BE(width, 0);
  ihdrData.writeUInt32BE(height, 4);
  ihdrData[8] = 8;  // bit depth
  ihdrData[9] = 2;  // color type (RGB)
  ihdrData[10] = 0; // compression
  ihdrData[11] = 0; // filter
  ihdrData[12] = 0; // interlace
  const ihdr = createChunk('IHDR', ihdrData);

  // IDAT chunk (image data)
  const filteredData = Buffer.alloc(height * (1 + width * 3));
  for (let y = 0; y < height; y++) {
    filteredData[y * (1 + width * 3)] = 0; // filter type: None
    for (let x = 0; x < width * 3; x++) {
      filteredData[y * (1 + width * 3) + 1 + x] = rawData[y * width * 3 + x];
    }
  }
  const compressed = zlib.deflateSync(filteredData);
  const idat = createChunk('IDAT', compressed);

  // IEND chunk
  const iend = createChunk('IEND', Buffer.alloc(0));

  // 组合所有部分
  return Buffer.concat([signature, ihdr, idat, iend]);
}

function createChunk(type, data) {
  const length = Buffer.alloc(4);
  length.writeUInt32BE(data.length, 0);

  const typeBuffer = Buffer.from(type, 'ascii');
  const crcData = Buffer.concat([typeBuffer, data]);
  const crc = crc32(crcData);

  const crcBuffer = Buffer.alloc(4);
  crcBuffer.writeUInt32BE(crc >>> 0, 0);

  return Buffer.concat([length, typeBuffer, data, crcBuffer]);
}

function crc32(data) {
  let crc = 0xFFFFFFFF;
  const table = [];

  for (let n = 0; n < 256; n++) {
    let c = n;
    for (let k = 0; k < 8; k++) {
      if (c & 1) {
        c = 0xEDB88320 ^ (c >>> 1);
      } else {
        c = c >>> 1;
      }
    }
    table[n] = c;
  }

  for (let i = 0; i < data.length; i++) {
    crc = table[(crc ^ data[i]) & 0xFF] ^ (crc >>> 8);
  }

  return crc ^ 0xFFFFFFFF;
}

createIcon();
