/* 纯工具函数, 无模块依赖。 */

export const TYPE_LABELS = {
  // 人物
  person: '人物',
  character: '人物',
  // 地点/文明
  place: '地点',
  civilization: '文明',
  species: '物种',
  // 科技/设备
  technology: '科技',
  weapon: '武器',
  artifact: '设备',
  // 组织
  organization: '组织',
  faction: '阵营',
  // 事件
  event: '事件',
  // 物理/科学概念
  concept: '概念',
  law: '法则',
  theory: '理论',
  // 书册/作品
  book: '卷册',
  // 时间
  time: '时间',
  era: '纪元',
  // 页面类型
  topic: '主题',
  overview: '综述',
  story: '故事',
  list: '列表',
  disambiguation: '消歧义',
  redirect: '重定向',
  special: '特殊页面',
  meta: '元页',
  unknown: '未知',
};

export function escapeHtml(s) {
  return String(s).replace(/[&<>"']/g, (c) =>
    ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
}

export function escapeAttr(s) { return escapeHtml(s); }

export function setStatus(msg) {
  const el = document.getElementById('status');
  if (el) el.textContent = msg;
}

export function showFatal(msg) {
  const article = document.getElementById('article');
  if (article) {
    article.innerHTML = `<h1>错误</h1><p class="error">${escapeHtml(msg)}</p>`;
  }
  setStatus('');
}
