const { app, Tray, Menu, nativeImage, Notification } = require('electron');
const { exec } = require('child_process');
const path = require('path');

// 每日 500 万 Tokens
const DAILY_LIMIT = 5_000_000;

// 获取今日 Token 使用量
// 计算方式：inputTokens + outputTokens
// 官方文档说明：输入和输出 Tokens 均计入消耗
// 注意：此计算可能偏小，因为：
// 1. cacheReadTokens（缓存读取）也占用 API 资源，但通常不计入主计费
// 2. 系统提示词、工具调用结果等可能未完全统计
// 3. 某些中间过程（如重试、错误请求）可能产生额外消耗
async function getTodayUsage() {
  return new Promise((resolve, reject) => {
    const today = new Date().toISOString().split('T')[0];
    exec(`ccusage daily --json -s ${today} -u ${today}`, { encoding: 'utf8' }, (error, stdout) => {
      if (error) {
        reject(error);
        return;
      }
      try {
        const data = JSON.parse(stdout);
        // 计算 inputTokens + outputTokens
        const inputTokens = data.totals.inputTokens || 0;
        const outputTokens = data.totals.outputTokens || 0;
        const totalTokens = inputTokens + outputTokens;

        // 调试输出（可选）
        console.log(`[Debug] inputTokens: ${inputTokens}, outputTokens: ${outputTokens}, cacheReadTokens: ${data.totals.cacheReadTokens || 0}`);

        resolve(totalTokens);
      } catch (e) {
        reject(e);
      }
    });
  });
}

// 格式化数字（添加千位分隔符）
function formatNumber(num) {
  return num.toLocaleString('zh-CN');
}

// 根据使用比例获取状态颜色
function getStatusColor(percentage) {
  if (percentage >= 80) return '🔴';
  if (percentage >= 50) return '🟡';
  return '🟢';
}

// 更新托盘显示
async function updateTray() {
  try {
    const used = await getTodayUsage();
    const remaining = Math.max(0, DAILY_LIMIT - used);
    const percentage = ((used / DAILY_LIMIT) * 100).toFixed(1);
    const statusIcon = getStatusColor(parseFloat(percentage));

    // 更新托盘提示文本
    tray.setToolTip(
      `${statusIcon} LongCat API 监控\n` +
      `━━━━━━━━━━━━━━━━\n` +
      `📊 今日已用: ${formatNumber(used)}\n` +
      `💰 剩余额度: ${formatNumber(remaining)}\n` +
      `📈 使用比例: ${percentage}%`
    );

    // 更新托盘标题（显示在图标旁边，Windows 上可能不显示）
    tray.setTitle(`${percentage}%`);

    // 超过 80% 发送通知
    if (parseFloat(percentage) >= 80 && !notificationSent) {
      const notification = new Notification({
        title: 'LongCat API 使用警告',
        body: `今日已使用 ${percentage}% (${formatNumber(used)}/${formatNumber(DAILY_LIMIT)})`,
        icon: path.join(__dirname, 'tray-icon.png')
      });
      notification.show();
      notificationSent = true;
    }

    // 重置通知标记（新的一天）
    if (parseFloat(percentage) < 80) {
      notificationSent = false;
    }

    console.log(`[${new Date().toLocaleTimeString()}] 已更新: ${percentage}%`);
  } catch (error) {
    console.error('获取使用量失败:', error);
    tray.setToolTip('❌ LongCat API 监控\n获取数据失败，请检查 ccusage 是否安装');
  }
}

// 创建托盘
let tray = null;
let notificationSent = false;

app.whenReady().then(() => {
  // 创建托盘图标
  const iconPath = path.join(__dirname, 'tray-icon.png');

  // 如果图标不存在，创建一个默认图标
  let icon;
  try {
    icon = nativeImage.createFromPath(iconPath);
    if (icon.isEmpty()) {
      throw new Error('图标为空');
    }
  } catch (e) {
    console.log('使用默认图标');
    // 创建一个简单的默认图标（16x16 蓝色方块）
    icon = nativeImage.createEmpty();
  }

  tray = new Tray(icon);

  // 创建右键菜单
  const contextMenu = Menu.buildFromTemplate([
    {
      label: '🔄 刷新数据',
      click: updateTray,
    },
    { type: 'separator' },
    {
      label: '📊 打开详细报告',
      click: () => {
        const today = new Date().toISOString().split('T')[0];
        exec(`ccusage daily -s ${today} -u ${today}`);
      },
    },
    { type: 'separator' },
    {
      label: '❌ 退出',
      click: () => app.quit(),
    },
  ]);

  tray.setContextMenu(contextMenu);
  tray.setToolTip('LongCat API 监控\n正在加载...');

  // 初始更新
  updateTray();

  // 每 5 分钟自动刷新一次
  setInterval(updateTray, 5 * 60 * 1000);

  console.log('LongCat Monitor 已启动');
});

app.on('window-all-closed', () => {
  // macOS 上保持应用在托盘中运行
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

// 防止多个实例
const gotTheLock = app.requestSingleInstanceLock();
if (!gotTheLock) {
  app.quit();
} else {
  app.on('second-instance', () => {
    // 如果用户尝试运行第二个实例，不做任何事
  });
}
