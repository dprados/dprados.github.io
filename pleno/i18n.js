/* Pleno · tiny i18n for static pages. No dependencies.
   Strings live in window.PLENO_STRINGS = { en: {...}, es: {...}, fr: {...}, it: {...} }.
   Attributes: data-i18n (text), data-i18n-html (markup), data-i18n-alt, data-i18n-aria,
   data-i18n-title (title attribute), data-shot (per-locale screenshot), data-keep-lang (internal link). */
(function () {
  'use strict';
  var SUPPORTED = ['en', 'es', 'fr', 'it'];
  var STORE_KEY = 'pleno.lang';
  var SHOT_LOCALE = { en: 'en-US', es: 'es-ES', fr: 'fr-FR', it: 'it' };
  var S = window.PLENO_STRINGS || {};

  function norm(code) {
    if (!code) return null;
    var base = String(code).toLowerCase().split(/[-_]/)[0];
    if (base === 'ca' || base === 'eu' || base === 'gl') return 'es';
    return SUPPORTED.indexOf(base) >= 0 ? base : null;
  }
  function readStored() { try { return norm(localStorage.getItem(STORE_KEY)); } catch (e) { return null; } }
  function store(lang) { try { localStorage.setItem(STORE_KEY, lang); } catch (e) { /* private mode */ } }

  function detect() {
    var q = null;
    try { q = norm(new URLSearchParams(location.search).get('lang')); } catch (e) { /* old browser */ }
    if (q) return q;
    var saved = readStored();
    if (saved) return saved;
    var list = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language];
    for (var i = 0; i < list.length; i++) { var n = norm(list[i]); if (n) return n; }
    return 'en';
  }

  function t(lang, key) {
    var d = S[lang] || {};
    if (Object.prototype.hasOwnProperty.call(d, key)) return d[key];
    var en = S.en || {};
    return Object.prototype.hasOwnProperty.call(en, key) ? en[key] : null;
  }

  function each(sel, fn) { var n = document.querySelectorAll(sel); for (var i = 0; i < n.length; i++) fn(n[i]); }

  function apply(lang) {
    document.documentElement.lang = lang;
    each('[data-i18n]', function (el) { var v = t(lang, el.getAttribute('data-i18n')); if (v !== null) el.textContent = v; });
    each('[data-i18n-html]', function (el) { var v = t(lang, el.getAttribute('data-i18n-html')); if (v !== null) el.innerHTML = v; });
    each('[data-i18n-alt]', function (el) { var v = t(lang, el.getAttribute('data-i18n-alt')); if (v !== null) el.alt = v; });
    each('[data-i18n-aria]', function (el) { var v = t(lang, el.getAttribute('data-i18n-aria')); if (v !== null) el.setAttribute('aria-label', v); });
    each('[data-i18n-title]', function (el) { var v = t(lang, el.getAttribute('data-i18n-title')); if (v !== null) el.title = v; });
    var title = t(lang, 'meta.title'); if (title) document.title = title;
    var desc = t(lang, 'meta.desc');
    var md = document.querySelector('meta[name="description"]'); if (desc && md) md.setAttribute('content', desc);
    var loc = SHOT_LOCALE[lang];
    each('[data-shot]', function (el) {
      var src = el.getAttribute('data-shot').replace('{loc}', loc);
      if (el.getAttribute('src') !== src) el.setAttribute('src', src);
    });
    each('[data-keep-lang]', function (el) {
      var base = el.getAttribute('data-keep-lang');
      el.setAttribute('href', base + (base.indexOf('?') >= 0 ? '&' : '?') + 'lang=' + lang);
    });
    each('[data-lang-btn]', function (el) {
      el.setAttribute('aria-pressed', el.getAttribute('data-lang-btn') === lang ? 'true' : 'false');
    });
    document.documentElement.setAttribute('data-lang', lang);
    if (typeof window.onPlenoLang === 'function') window.onPlenoLang(lang);
  }

  function choose(lang) {
    store(lang);
    try {
      var u = new URL(location.href); u.searchParams.set('lang', lang);
      history.replaceState(null, '', u.pathname + u.search + u.hash);
    } catch (e) { /* ignore */ }
    apply(lang);
  }

  document.addEventListener('click', function (ev) {
    var b = ev.target.closest ? ev.target.closest('[data-lang-btn]') : null;
    if (b) { ev.preventDefault(); choose(b.getAttribute('data-lang-btn')); }
  });

  window.PlenoI18n = { apply: apply, choose: choose, lang: detect() };
  apply(window.PlenoI18n.lang);
})();
