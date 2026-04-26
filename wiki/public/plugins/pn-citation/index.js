/**
 * pn-citation — 三体 PN 段落引文插件
 *
 * PN 格式：B-CC-PPP
 *   B   = 书号 (1/2/3)
 *   CC  = 章节序号 (01–51，书内全局递增)
 *   PPP = 段落序号 (001–999)
 *
 * 功能：
 *   1. 段落锚点：将 <p>[1-02-001] 文字</p> → <p id="pn-1-02-001">文字</p>
 *   2. 引文链接：将 （1-02-001） → 可点击链接，跳转章节页并滚动到段落
 *
 * Hook: onAfterRender
 */

const PLUGIN_NAME = 'pn-citation';

// 匹配段落开头的 PN 标签，如 [1-02-001]
const RE_PN_TAG = /<p>\[(\d-\d{2}-\d{3})\]\s*/g;

// 匹配引文写法 （1-02-001）（全角括号）
const RE_CITATION_PLAIN = /（(\d)-(\d{2})-(\d{3})）/g;

// 匹配 wikilink 已展开形式：（<a ...>1-02-001</a>）
const RE_CITATION_WIKILINK = /（<a\s[^>]*class="wikilink[^"]*"[^>]*>(\d)-(\d{2})-(\d{3})<\/a>）/g;

function expandAnchors(html) {
  return html.replace(RE_PN_TAG, '<p id="pn-$1">');
}

function expandCitations(html, chapterMap) {
  // 1. wikilink 展开形式
  html = html.replace(RE_CITATION_WIKILINK, (_match, b, cc, ppp) => {
    return buildCitationLink(b, cc, ppp, chapterMap) ?? _match;
  });

  // 2. 纯文本形式（保护已有 <a> 标签内的内容）
  const anchors = [];
  const protected_ = html.replace(/<a[\s\S]*?<\/a>/g, m => {
    anchors.push(m);
    return `\x00a${anchors.length - 1}\x00`;
  });

  const expanded = protected_.replace(RE_CITATION_PLAIN, (_match, b, cc, ppp) => {
    return buildCitationLink(b, cc, ppp, chapterMap) ?? _match;
  });

  return expanded.replace(/\x00a(\d+)\x00/g, (_, i) => anchors[+i]);
}

function buildCitationLink(b, cc, ppp, chapterMap) {
  const prefix = `${b}-${cc}`;
  const pageId = chapterMap[prefix];
  if (!pageId) return null;

  const pn = `${b}-${cc}-${ppp}`;
  const href = `#${encodeURIComponent(pageId)}`;
  const label = pn;
  const bookLabel = ['', '三体I', '三体II', '三体III'][+b] || `三体${b}`;
  const title = `${bookLabel} §${cc} ¶${+ppp}`;

  return `（<a class="pn-citation" href="${href}" data-pn="pn-${pn}" title="${title}">${label}</a>）`;
}

export default {
  name: PLUGIN_NAME,
  version: '1.0.0',

  async init(core) {
    let chapterMap = null;

    core.hooks.onBoot.add(async () => {
      try {
        const r = await fetch('data/chapter_map.json');
        chapterMap = await r.json();
        console.log(`[${PLUGIN_NAME}] 加载 ${Object.keys(chapterMap).length} 个章节映射`);
      } catch (e) {
        console.warn(`[${PLUGIN_NAME}] 无法加载 data/chapter_map.json:`, e);
      }
    });

    core.hooks.onAfterRender.add((html) => {
      html = expandAnchors(html);
      if (chapterMap) html = expandCitations(html, chapterMap);
      return html;
    });

    // 跨页滚动：点击引文链接时存 PN，页面加载后滚动到目标段落
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a.pn-citation');
      if (!a || !a.dataset.pn) return;
      const currentPage = decodeURIComponent(location.hash.slice(1));
      const targetPage = decodeURIComponent((a.getAttribute('href') || '').slice(1));
      if (currentPage === targetPage) {
        // 同页：直接滚动
        e.preventDefault();
        const el = document.getElementById(a.dataset.pn);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      } else {
        // 跨页：存 PN，导航后自动滚动
        sessionStorage.setItem('pendingPN', a.dataset.pn);
      }
    });

    // 跨页导航后，等待 DOM 渲染完成再滚动
    window.addEventListener('hashchange', () => {
      const pending = sessionStorage.getItem('pendingPN');
      if (!pending) return;
      sessionStorage.removeItem('pendingPN');
      const tryScroll = (attempts = 0) => {
        const el = document.getElementById(pending);
        if (el) {
          el.scrollIntoView({ behavior: 'smooth', block: 'center' });
          el.classList.add('pn-highlight');
          setTimeout(() => el.classList.remove('pn-highlight'), 2000);
        } else if (attempts < 25) {
          setTimeout(() => tryScroll(attempts + 1), 80);
        }
      };
      setTimeout(tryScroll, 100);
    });

    // 暴露给其他插件（如 semantic-block）
    core.pnCitation = {
      expand: (html) => {
        html = expandAnchors(html);
        return chapterMap ? expandCitations(html, chapterMap) : html;
      },
    };
  },
};
