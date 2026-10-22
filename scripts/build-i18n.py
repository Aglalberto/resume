#!/usr/bin/env python3
"""Gera as páginas de cada idioma a partir de locales/*.json.

    python3 scripts/build-i18n.py

- index.html é o modelo E a página em PT: os textos dos elementos com
  data-i18n* são reescritos a partir de locales/pt-BR.json (rodar de novo
  não muda nada se os JSONs não mudaram).
- en/index.html é gerado a partir do mesmo modelo + locales/en.json.
  Não edite en/index.html à mão.
- Valida: mesmas chaves em todos os idiomas e nenhuma chave usada no HTML
  faltando nos JSONs.

Marcação suportada no HTML:
  data-i18n="a.b"          texto (escapado)
  data-i18n-html="a.b"     HTML interno
  data-i18n-list="a.b"     array -> <li>…</li>
  data-i18n-type="a.b"     texto da máquina de escrever (renderizado para SEO)
  data-i18n-attr="alt:a.b;title:c.d"
  data-i18n-href="a.b"
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = 'https://aglalberto.com'
LANGS = [  # (código, pasta de saída, og:locale)
    ('pt-BR', '', 'pt_BR'),
    ('en', 'en', 'en_US'),
]
DEFAULT = 'pt-BR'

TAG = re.compile(r'<(/?)([a-zA-Z0-9]+)\b([^>]*)>')
I18N_ATTR = re.compile(r'\sdata-i18n(-html|-list|-type|-attr|-href)?="([^"]*)"')


def fail(msg):
    print('ERRO:', msg)
    sys.exit(1)


def load(lang):
    path = os.path.join(ROOT, 'locales', lang + '.json')
    with open(path, encoding='utf-8') as f:
        return json.load(f)


def flatten(d, prefix=''):
    out = {}
    for k, v in d.items():
        if k.startswith('_'):
            continue
        key = prefix + k
        if isinstance(v, dict):
            out.update(flatten(v, key + '.'))
        else:
            out[key] = v
    return out


def script_ranges(s):
    return [(m.start(), m.end()) for m in re.finditer(r'<(script|style)\b.*?</\1>', s, re.S)]


def match_close(s, start, name):
    depth = 0
    for m in TAG.finditer(s, start):
        if m.group(2).lower() != name:
            continue
        if m.group(1) == '' and not m.group(3).rstrip().endswith('/'):
            depth += 1
        elif m.group(1) == '/':
            depth -= 1
            if depth == 0:
                return m.start()
    fail('tag <%s> sem fechamento (posição %d)' % (name, start))


def set_attr(stag, name, value):
    value = html.escape(value, quote=True)
    if re.search(r'\s%s="[^"]*"' % re.escape(name), stag):
        return re.sub(r'(\s%s=")[^"]*(")' % re.escape(name), lambda m: m.group(1) + value + m.group(2), stag, count=1)
    return stag[:-1].rstrip() + ' %s="%s">' % (name, value)


def collect_keys(s):
    keys = set()
    for m in I18N_ATTR.finditer(s):
        if m.group(1) == '-attr':
            for part in m.group(2).split(';'):
                if part.strip():
                    keys.add(part.split(':', 1)[1].strip())
        else:
            keys.add(m.group(2))
    return keys


def render(s, d):
    """Reescreve conteúdo/atributos de todo elemento com data-i18n*."""
    ranges = script_ranges(s)
    items = []
    for m in TAG.finditer(s):
        if m.group(1) or not I18N_ATTR.search(m.group(0)):
            continue
        if any(a <= m.start() < b for a, b in ranges):
            continue
        items.append(m)
    # de trás pra frente: os índices anteriores continuam válidos
    for m in reversed(items):
        stag, name = m.group(0), m.group(2).lower()
        attrs = {g1 or '': g2 for g1, g2 in I18N_ATTR.findall(stag)}
        new_stag = stag
        if '-attr' in attrs:
            for part in attrs['-attr'].split(';'):
                if not part.strip():
                    continue
                attr, key = [x.strip() for x in part.split(':', 1)]
                new_stag = set_attr(new_stag, attr, d[key])
        if '-href' in attrs:
            new_stag = set_attr(new_stag, 'href', d[attrs['-href']])
        content = None
        if '' in attrs:
            content = html.escape(d[attrs['']], quote=False)
        elif '-type' in attrs:
            content = html.escape(d[attrs['-type']], quote=False)
        elif '-html' in attrs:
            content = d[attrs['-html']]
        elif '-list' in attrs:
            vals = d[attrs['-list']]
            if not isinstance(vals, list):
                fail('%s deveria ser uma lista' % attrs['-list'])
            content = ''.join('<li>%s</li>' % html.escape(v, quote=False) for v in vals)
        if content is None:
            s = s[:m.start()] + new_stag + s[m.end():]
        else:
            close = match_close(s, m.start(), name)
            s = s[:m.start()] + new_stag + content + s[close:]
    return s


def head_block(lang, d, all_langs):
    def url(code):
        folder = next(f for c, f, _ in LANGS if c == code)
        return SITE + '/' + (folder + '/' if folder else '')
    og_locale = next(o for c, _, o in LANGS if c == lang)
    title, desc = html.escape(d['meta.titulo']), html.escape(d['meta.descricao'])
    lines = [
        '<!-- i18n:head — gerado por scripts/build-i18n.py, não editar à mão -->',
        '<title>%s</title>' % title,
        '<meta name="description" content="%s">' % desc,
        '<link rel="canonical" href="%s">' % url(lang),
    ]
    for code in all_langs:
        lines.append('<link rel="alternate" hreflang="%s" href="%s">' % (code, url(code)))
    lines.append('<link rel="alternate" hreflang="x-default" href="%s">' % url(DEFAULT))
    lines += [
        '<meta property="og:type" content="website">',
        '<meta property="og:title" content="%s">' % title,
        '<meta property="og:description" content="%s">' % desc,
        '<meta property="og:url" content="%s">' % url(lang),
        '<meta property="og:locale" content="%s">' % og_locale,
    ]
    return '\n    '.join(lines)


def main():
    src_path = os.path.join(ROOT, 'index.html')
    with open(src_path, encoding='utf-8') as f:
        template = f.read()

    raw = {code: load(code) for code, _, _ in LANGS}
    flat = {code: flatten(raw[code]) for code in raw}

    # 1) mesmas chaves em todos os idiomas
    base = set(flat[DEFAULT])
    for code in flat:
        missing, extra = base - set(flat[code]), set(flat[code]) - base
        if missing:
            fail('%s.json sem as chaves: %s' % (code, ', '.join(sorted(missing))))
        if extra:
            fail('%s.json tem chaves que não existem em %s.json: %s' % (code, DEFAULT, ', '.join(sorted(extra))))

    # 2) toda chave usada no HTML existe
    used = collect_keys(template)
    for code in flat:
        missing = used - set(flat[code])
        if missing:
            fail('chaves usadas no HTML e ausentes em %s.json: %s' % (code, ', '.join(sorted(missing))))

    # 3) nada do sistema antigo sobrando
    if re.search(r'class="[^"]*\blang-(pt|en)\b', template) or 'data-text-pt=' in template or 'data-href-pt=' in template:
        fail('sobrou marcação antiga (lang-pt/lang-en, data-text-*, data-href-*) no index.html')

    if '<!-- i18n:head' not in template or '<!-- /i18n:head -->' not in template:
        fail('marcadores <!-- i18n:head --> ... <!-- /i18n:head --> não encontrados')
    if '<!-- i18n:dict -->' not in template or '<!-- /i18n:dict -->' not in template:
        fail('marcadores <!-- i18n:dict --> ... <!-- /i18n:dict --> não encontrados')

    codes = [c for c, _, _ in LANGS]
    for code, folder, _ in LANGS:
        d = flat[code]
        out = render(template, d)
        out = re.sub(r'<html lang="[^"]*"', '<html lang="%s"' % code, out, count=1)
        out = re.sub(r'<!-- i18n:head.*?<!-- /i18n:head -->',
                     lambda m: head_block(code, d, codes) + '\n    <!-- /i18n:head -->', out, count=1, flags=re.S)
        dict_json = json.dumps(raw[code], ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
        out = re.sub(r'<!-- i18n:dict -->.*?<!-- /i18n:dict -->',
                     lambda m: '<!-- i18n:dict -->\n    <script type="application/json" id="i18n-current">%s</script>\n    <!-- /i18n:dict -->' % dict_json,
                     out, count=1, flags=re.S)
        dest = os.path.join(ROOT, folder, 'index.html') if folder else src_path
        if folder:
            os.makedirs(os.path.join(ROOT, folder), exist_ok=True)
        with open(dest, 'w', encoding='utf-8') as f:
            f.write(out)
        print('ok  %-6s -> %s' % (code, os.path.relpath(dest, ROOT)))

    # sitemap com as versões alternativas
    urls = []
    for code, folder, _ in LANGS:
        loc = SITE + '/' + (folder + '/' if folder else '')
        alts = ''.join('\n    <xhtml:link rel="alternate" hreflang="%s" href="%s"/>' % (c, SITE + '/' + (f + '/' if f else '')) for c, f, _ in LANGS)
        urls.append('  <url>\n    <loc>%s</loc>%s\n  </url>' % (loc, alts))
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
               + '\n'.join(urls) + '\n</urlset>\n')
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w', encoding='utf-8') as f:
        f.write(sitemap)
    print('ok  sitemap.xml  (%d chaves por idioma)' % len(base))


if __name__ == '__main__':
    main()
