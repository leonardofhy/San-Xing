/**
 * Showdown.js - A Markdown to HTML converter (Global Scope Fixed for Google Apps Script)
 * Copyright (c) 2007-2018, John Fraser
 * All rights reserved.
 * @version 1.9.1
 * This version contains internal fixes to make it compatible with Google Apps Script.
 */

var showdown = (function () {
  'use strict';

  function getDefaultOpts(simple) {
    var defaultOptions = {
      omitExtraWLInCodeBlocks: { defaultValue: false, type: 'boolean' },
      noHeaderId: { defaultValue: false, type: 'boolean' },
      prefixHeaderId: { defaultValue: false, type: 'string' },
      ghCompatibleHeaderId: { defaultValue: false, type: 'boolean' },
      headerLevelStart: { defaultValue: false, type: 'integer' },
      parseImgDimensions: { defaultValue: false, type: 'boolean' },
      simplifiedAutoLink: { defaultValue: false, type: 'boolean' },
      excludeTrailingPunctuationFromURLs: { defaultValue: false, type: 'boolean' },
      literalMidWordUnderscores: { defaultValue: false, type: 'boolean' },
      strikethrough: { defaultValue: false, type: 'boolean' },
      tables: { defaultValue: false, type: 'boolean' },
      tablesHeaderId: { defaultValue: false, type: 'boolean' },
      ghCodeBlocks: { defaultValue: true, type: 'boolean' },
      tasklists: { defaultValue: false, type: 'boolean' },
      simpleLineBreaks: { defaultValue: false, type: 'boolean' },
      requireSpaceBeforeHeadingText: { defaultValue: false, type: 'boolean' },
      ghMentions: { defaultValue: false, type: 'boolean' },
      ghMentionsLink: { defaultValue: 'https://github.com/{u}', type: 'string' },
      encodeEmails: { defaultValue: true, type: 'boolean' },
      openLinksInNewWindow: { defaultValue: false, type: 'boolean' },
      backslashEscapesHTMLTags: { defaultValue: false, type: 'boolean' },
      emoji: { defaultValue: false, type: 'boolean' },
      underline: { defaultValue: false, type: 'boolean' }
    };
    if (simple === false) { return JSON.parse(JSON.stringify(defaultOptions)); }
    var ret = {};
    for (var opt in defaultOptions) { if (defaultOptions.hasOwnProperty(opt)) { ret[opt] = defaultOptions[opt].defaultValue; } }
    return ret;
  }

  function obAssign(ob, options) {
    if (!ob) { throw new Error('ob parameter cannot be null or undefined'); }
    for (var opt in options) { if (options.hasOwnProperty(opt)) { ob[opt] = options[opt]; } }
    return ob;
  }

  function isUndefined(a) { return (typeof a === 'undefined'); }

  var showdown = {
    version: '1.9.1',
    Converter: (function () {
      function C(options) {
        this.options = options || {};
        this.globals = {};
        this.setOption = function(key, value) { this.options[key] = value; };
        this.getOption = function(key) { return this.options[key]; };
        this.getOptions = function() { return this.options; };
        this.makeHtml = function(text) {
          this.globals = { gHtmlBlocks: [], gUrls: {}, gTitles: {}, gDimensions: {}, gListLevel: 0 };
          if (isUndefined(text)) text = '';
          text = text.replace(/¨/g, '¨T');
          text = text.replace(/\$/g, '¨D');
          text = text.replace(/\r\n/g, '\n');
          text = text.replace(/\r/g, '\n');
          text = '\n\n' + text + '\n\n';
          
          // [內部呼叫修正]
          text = showdown.subParser_detab(text, this.options, this.globals);
          text = showdown.subParser_stripBlankLines(text, this.options, this.globals);
          text = showdown.subParser_githubCodeBlocks(text, this.options, this.globals);
          text = showdown.subParser_hashHTMLBlocks(text, this.options, this.globals);
          text = showdown.subParser_stripLinkDefinitions(text, this.options, this.globals);
          text = showdown.subParser_blockGamut(text, this.options, this.globals);
          text = showdown.subParser_unhashHTMLSpans(text, this.options, this.globals);
          text = showdown.subParser_unescapeSpecialChars(text, this.options, this.globals);

          text = text.replace(/¨D/g, '$$');
          text = text.replace(/¨T/g, '¨');
          return text;
        };
        obAssign(this.options, getDefaultOpts(true));
        if (options) obAssign(this.options, options);
      }
      return C;
    }()),
    subParser: function (name, func) {
      // The registration function remains the same
      if (showdown.hasOwnProperty('subParser_' + name)) {
        // This log is useful for debugging library issues.
        // console.log('SubParser ' + name + ' has been overwritten.');
      }
      showdown['subParser_' + name] = func;
    }
  };
  
  // Define all sub-parsers by attaching them to the showdown object
  showdown.subParser('detab', function (text) { return text.replace(/\t/g, '    '); });
  showdown.subParser('stripBlankLines', function (text) { return text.replace(/^[ \t]+$/gm, ''); });
  showdown.subParser('githubCodeBlocks', function (text, options, globals) {
    if (options.ghCodeBlocks) {
      return text.replace(/(?:^|\n)```(.*)\n([\s\S]*?)\n```/g, function (wholeMatch, lang, code) {
        var endChar = (options.omitExtraWLInCodeBlocks) ? '' : '\n';
        code = showdown.subParser_encodeCode(code);
        code = showdown.subParser_detab(code);
        code = code.replace(/^\n+/, '').replace(/\n+$/, '');
        var preClass = lang ? ' class="' + lang + ' language-' + lang + '"' : '';
        var codeBlock = '<pre><code' + preClass + '>' + code + endChar + '</code></pre>';
        return '\n\n¨G' + (globals.gHtmlBlocks.push(codeBlock) - 1) + 'G\n\n';
      });
    }
    return text;
  });
  showdown.subParser('hashHTMLBlocks', function (text, options, globals) {
    var blockTags = ['pre', 'div', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'table', 'dl', 'ol', 'ul', 'script', 'iframe', 'ins', 'del', 'p'];
    for (var i = 0; i < blockTags.length; ++i) {
      var r = new RegExp('^<s*' + blockTags[i] + '[\\s\\S]*?<\\/' + blockTags[i] + 's*>$', 'gim');
      text = text.replace(r, function (wholeMatch) {
        return '\n\n¨G' + (globals.gHtmlBlocks.push(wholeMatch) - 1) + 'G\n\n';
      });
    }
    return text;
  });
  showdown.subParser('stripLinkDefinitions', function (text, options, globals) {
    var rx = /^ {0,3}\[([^\]]+)]:[ \t]*\n?[ \t]*<?([^>\s]+)>?(?:[ \t]*\n?[ \t]*((['"])([^>]+?)\4))?[ \t]*/gm;
    return text.replace(rx, function (wholeMatch, linkId, url, a, b, title) {
      linkId = linkId.toLowerCase();
      globals.gUrls[linkId] = showdown.subParser_encodeAmpsAndAngles(url);
      if (title) { globals.gTitles[linkId] = title.replace(/"|'/g, '&quot;'); }
      return '';
    });
  });
  showdown.subParser('blockGamut', function (text, options, globals) {
    text = showdown.subParser_headers(text, options, globals);
    text = showdown.subParser_horizontalRule(text, options, globals);
    text = showdown.subParser_lists(text, options, globals);
    text = showdown.subParser_codeBlocks(text, options, globals);
    text = showdown.subParser_blockQuotes(text, options, globals);
    text = showdown.subParser_tables(text, options, globals);
    text = showdown.subParser_hashHTMLBlocks(text, options, globals);
    text = showdown.subParser_formParagraphs(text, options, globals);
    return text;
  });
  showdown.subParser('unhashHTMLSpans', function (text, options, globals) {
    for (var i = 0; i < globals.gHtmlBlocks.length; ++i) {
      text = text.replace('¨G' + i + 'G', globals.gHtmlBlocks[i]);
    }
    return text;
  });
  showdown.subParser('unescapeSpecialChars', function(text) {
    return text.replace(/¨E(\d+)E/g, function(wholeMatch, m1) {
      return String.fromCharCode(parseInt(m1));
    });
  });
  showdown.subParser('encodeAmpsAndAngles', function (text) {
    text = text.replace(/&(?!#?[xX]?(?:[0-9a-fA-F]+|\w+);)/g, '&amp;');
    text = text.replace(/<(?![a-z\/?\$!])/gi, '&lt;');
    return text;
  });
  showdown.subParser('encodeCode', function (text) {
    text = text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
    return text.replace(/([*_{}\[\]\\=~-])/g, function(wholeMatch, m1) {
      return '¨E' + m1.charCodeAt(0) + 'E';
    });
  });
  showdown.subParser('headers', function (text, options, globals) {
    var headerLevelStart = isNaN(parseInt(options.headerLevelStart)) ? 1 : parseInt(options.headerLevelStart);
    var setextRegexH1 = /^(.+)[ \t]*\n=+[ \t]*\n+/gm;
    var setextRegexH2 = /^(.+)[ \t]*\n-+[ \t]*\n+/gm;
    text = text.replace(setextRegexH1, function (wm, m1) { return '<h1>' + showdown.subParser_spanGamut(m1, options, globals) + '</h1>'; });
    text = text.replace(setextRegexH2, function (wm, m1) { return '<h2>' + showdown.subParser_spanGamut(m1, options, globals) + '</h2>'; });
    var atxStyle = (options.requireSpaceBeforeHeadingText) ? /^(#{1,6})[ \t]+(.+?)[ \t]*#*\n+/gm : /^(#{1,6})[ \t]*(.+?)[ \t]*#*\n+/gm;
    text = text.replace(atxStyle, function (wm, m1, m2) {
      var hLevel = headerLevelStart + m1.length - 1;
      return '<h' + hLevel + '>' + showdown.subParser_spanGamut(m2, options, globals) + '</h' + hLevel + '>\n';
    });
    return text;
  });
  showdown.subParser('horizontalRule', function (text) {
    return text.replace(/^ {0,2}( ?-){3,}[ \t]*$/gm, "\n<hr />\n");
  });
  showdown.subParser('lists', function (text, options, globals) {
    text += '¨0';
    var listRgx = /^(([ ]{0,3}([*+-]|\d+\.))[ \t]+)(?=\S)/gm;
    if (globals.gListLevel) {
      text = text.replace(listRgx, function (wholeMatch, m1) { return m1; });
    } else {
      var rgx = /(\n\n|^\n?)(([ ]{0,3}(([*+-]|\d+\.))[ \t]+)[^\r]+?(¨0|\n{2,}(?=\S)(?![ \t]*(?:[*+-]|\d+\.))[ \t]*))/g;
      text = text.replace(rgx, function(wholeMatch, m1, m2, m3) {
        var list = m2.replace(/\n{2,}/g, '\n\n\n');
        var listType = m3.search(/[*+-]/g) > -1 ? "ul" : "ol";
        var result = showdown.subParser_listItems(list, options, globals, listType);
        return '<' + listType + '>' + result + '</' + listType + '>\n\n';
      });
    }
    text = text.replace(/¨0/g, '');
    return text;
  });
  showdown.subParser('listItems', function (listStr, options, globals, listType) {
    globals.gListLevel++;
    listStr = listStr.replace(/\n{2,}/g, '\n');
    listStr += '¨0';
    var rgx = /(\n)?(^[ \t]*)([*+-]|\d+\.)[ \t]+([^\r]+?(\n{1,2})?)(?=\n*(¨0|\2([*+-]|\d+\.)[ \t]+))/gm;
    listStr = listStr.replace(rgx, function (wholeMatch, m1, m2, m3, m4) {
      var item = m4.replace(/\s+$/, '');
      item = showdown.subParser_blockGamut(item, options, globals);
      return '<li>' + item + '</li>\n';
    });
    listStr = listStr.replace(/¨0/g, '');
    globals.gListLevel--;
    return listStr;
  });
  showdown.subParser('blockQuotes', function (text, options, globals) {
    return text.replace(/((^[ \t]*>[ \t]?.+\n(.+\n)*\n*)+)/gm, function (wholeMatch) {
      var bq = wholeMatch;
      bq = bq.replace(/^[ \t]*>[ \t]?/gm, '');
      bq = showdown.subParser_blockGamut(bq, options, globals);
      return '<blockquote>\n' + bq + '\n</blockquote>\n\n';
    });
  });
  showdown.subParser('codeBlocks', function (text, options, globals) {
    return text.replace(/(?:\n\n|^)((?:(?:[ ]{4}|\t).*\n+)+)(\n*[ ]{0,3}[^ \t\n]|(?=¨0))/g, function (wholeMatch, m1) {
      var codeblock = showdown.subParser_encodeCode(m1);
      codeblock = showdown.subParser_detab(codeblock);
      codeblock = codeblock.replace(/^\n+/, '').replace(/\n+$/, '');
      return '\n\n¨G' + (globals.gHtmlBlocks.push('<pre><code>' + codeblock + '\n</code></pre>') - 1) + 'G\n\n';
    });
  });
  showdown.subParser('tables', function (text, options, globals) {
    if (!options.tables) { return text; }
    var leadingPipe = /^ {0,3}\|(.+)\n {0,3}\|(.*)\n((?: {0,3}\|.*(?:\n|$))+)/gm;
    var noLeadingPipe = /^ {0,3}(.+)\|(.+)\n {0,3}(?:[-:]+ *\|[-| :]*)\n((?:.*\|.*(?:\n|$))+)/gm;
    function _tablesCallback(wholeMatch, m1, m2, m3) {
      var headers = m1.replace(/^\| *| *\| *$/g, "").split(/ *\| */);
      var aligns = m2.replace(/^\| *| *\| *$/g, "").split(/ *\| */);
      var rows = m3.replace(/(?:^\||\| *$)/gm, "").split("\n");
      var a = [];
      for(var i=0; i<aligns.length; i++) {
        if (/^:[ \t-]*:$/.test(aligns[i])) a[i] = ' style="text-align:center;"';
        else if (/^:[ \t-]*$/.test(aligns[i])) a[i] = ' style="text-align:left;"';
        else if (/^[ \t-]*:$/.test(aligns[i])) a[i] = ' style="text-align:right;"';
        else a[i] = '';
      }
      var head = '<thead>\n<tr>\n';
      for(i=0; i<headers.length; i++) head += '<th' + a[i] + '>' + showdown.subParser_spanGamut(headers[i], options, globals) + '</th>\n';
      head += '</tr>\n</thead>\n';
      var body = '';
      for(i=0; i<rows.length; i++) {
        if(rows[i].trim() === '') continue;
        var r = rows[i].replace(/^\| *| *\| *$/g, "").split(/ *\| */);
        body += '<tr>\n';
        for(var j=0; j<headers.length; j++) body += '<td' + a[j] + '>' + showdown.subParser_spanGamut(r[j], options, globals) + '</td>\n';
        body += '</tr>\n';
      }
      return '<table>\n' + head + '<tbody>\n' + body + '</tbody>\n</table>\n';
    }
    text = text.replace(leadingPipe, _tablesCallback);
    text = text.replace(noLeadingPipe, _tablesCallback);
    return text;
  });
  showdown.subParser('spanGamut', function (text, options, globals) {
    text = showdown.subParser_codeSpans(text, options, globals);
    text = showdown.subParser_images(text, options, globals);
    text = showdown.subParser_anchors(text, options, globals);
    text = showdown.subParser_autoLinks(text, options, globals);
    text = showdown.subParser_encodeAmpsAndAngles(text);
    text = showdown.subParser_italicsAndBold(text, options, globals);
    text = showdown.subParser_hardLineBreaks(text, options, globals);
    return text;
  });
  showdown.subParser('codeSpans', function (text) {
    return text.replace(/(^|[^\\])(`+)(.+?[^`])\2(?!`)/gm, function (whole, p1, p2, p3) {
      return p1 + '<code>' + p3.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</code>';
    });
  });
  showdown.subParser('images', function (text, options, globals) {
    var inlineRegExp = /!\[(.*?)]\s?\([ \t]*()<?(\S+?)>?[ \t]*((['"])(.*?)\5[ \t]*)?\)/g;
    var referenceRegExp = /!\[(.*?)][ \t]*\[(.*?)?]/g;
    function writeImageTag(wholeMatch, altText, linkId, url, m5, m6, title) {
      var src = url, alt = altText, tit = title;
      if (linkId) {
        linkId = linkId.toLowerCase() || alt.toLowerCase();
        src = globals.gUrls[linkId];
        tit = globals.gTitles[linkId];
      }
      alt = alt.replace(/"/g, '&quot;');
      src = showdown.subParser_encodeAmpsAndAngles(src);
      return '<img src="' + src + '" alt="' + alt + '"' + (tit ? ' title="' + tit + '"' : '') + ' />';
    }
    text = text.replace(inlineRegExp, writeImageTag);
    text = text.replace(referenceRegExp, writeImageTag);
    return text;
  });
  showdown.subParser('anchors', function (text, options, globals) {
    var inlineRegExp = /\[(.*?)]\s?\([ \t]*()<?(\S+?)>?[ \t]*((['"])(.*?)\5[ \t]*)?\)/g;
    var referenceRegExp = /\[(.*?)]\s?\[(.*?)?]/g;
    function writeAnchorTag(wholeMatch, linkText, linkId, url, m5, m6, title) {
      var link = url, txt = linkText, tit = title;
      if (linkId) {
        linkId = linkId.toLowerCase() || txt.toLowerCase();
        link = globals.gUrls[linkId];
        tit = globals.gTitles[linkId];
      }
      txt = showdown.subParser_spanGamut(txt, options, globals);
      link = showdown.subParser_encodeAmpsAndAngles(link);
      return '<a href="' + link + '"' + (tit ? ' title="' + tit + '"' : '') + '>' + txt + '</a>';
    }
    text = text.replace(inlineRegExp, writeAnchorTag);
    text = text.replace(referenceRegExp, writeAnchorTag);
    return text;
  });
  showdown.subParser('autoLinks', function (text, options) {
    if (options.simplifiedAutoLink) {
        var simplifiedRegExp = /(^|\s)(https?:\/\/[^\s<>"]+)/g;
        text = text.replace(simplifiedRegExp, '$1<a href="$2">$2</a>');
    }
    return text;
  });
  showdown.subParser('italicsAndBold', function (text) {
    text = text.replace(/(\*\*|__)(?=\S)(.+?[*_]*)(?=\S)\1/g, '<strong>$2</strong>');
    text = text.replace(/(\*|_)(?=\S)(.+?)(?=\S)\1/g, '<em>$2</em>');
    return text;
  });
  showdown.subParser('hardLineBreaks', function (text, options) {
    if (options.simpleLineBreaks) { return text.replace(/\n/g, '<br />\n'); }
    return text.replace(/ {2,}\n/g, '<br />\n');
  });
  showdown.subParser('formParagraphs', function (text, options, globals) {
    text = text.replace(/^\n+/g, '').replace(/\n+$/g, '');
    var grafs = text.split(/\n{2,}/g);
    for (var i = 0; i < grafs.length; i++) {
        if (grafs[i].search(/¨G\d+G/) < 0) {
            grafs[i] = showdown.subParser_spanGamut(grafs[i], options, globals);
            grafs[i] = '<p>' + grafs[i].replace(/^\s*/, '').replace(/\s*$/, '') + '</p>';
        }
    }
    return grafs.join('\n\n');
  });

  return showdown;
}());
