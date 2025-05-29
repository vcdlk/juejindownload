// ==UserScript==
// @name         download for junjin
// @namespace    https://juejin.cn/
// @version      2025-05-29
// @description  try to take over the world!
// @author       vcdlk
// @match        https://juejin.cn/*
// @icon         https://img.88icon.com/download/jpg/20200908/3a6a03fd979e92a40dcb8c8de4810cf9_512_412.jpg!con
// @require https://cdn.bootcss.com/jquery/1.12.4/jquery.min.js
// @grant        GM_xmlhttpRequest
// @run-at       document-start
// ==/UserScript==

(function () {
  'use strict';
  let btn = document.createElement("button");
  btn.innerHTML = "download";
  btn.style = "position: fixed;z-index: 999; left: 90%; top: 20px;";

  btn.onclick = function () {
    saveContext()
  }

  window.addEventListener('load', () => {
    document.body.append(btn);
  });

  let aid, uuid;
  const originalFetch = unsafeWindow.fetch;

  unsafeWindow.fetch = async function (...args) {
    const req = args[0] instanceof Request ? args[0].clone() : new Request(args[0], args[1]);

    try {
      const fullUrl = new URL(req.url, location.href).href;

      if (fullUrl.startsWith('https://api.juejin.cn/booklet_api/v1/section/get')) {
        const urlObj = new URL(fullUrl);
        const params = urlObj.searchParams;

        aid = params.get('aid');
        uuid = params.get('uuid');
      }
    } catch (error) {
      console.warn('[参数捕获错误]', error);
    }

    return originalFetch.apply(this, args);
  };


  function buildApiUrl(aid, uuid, spider = 0) {
    return `https://api.juejin.cn/booklet_api/v1/section/get?aid=${aid}&uuid=${uuid}&spider=${spider}`;
  }

  function saveContext() {
    var url = window.location.href
    var path_segments = url.split("/")
    var book_id = path_segments[4]
    var section_id = path_segments[6];
    console.log(book_id);
    console.log(section_id);

    var json = { "section_id": section_id }

    let req_url = buildApiUrl(aid, uuid);

    console.log(req_url);
    const cookies = document.cookie;
    console.log("cookies:", cookies);


    GM_xmlhttpRequest({
      method: "POST",
      url: req_url,
      data: JSON.stringify(json),
      headers: {
        "Content-Type": "application/json"
      },
      onload: function (response) {
        const data = JSON.parse(response.responseText);
        const section = data.data.section;
        console.log("section:", section);
        var context = section.markdown_show;
        var title = section.draft_title;
        console.log("context:", context);
        console.log("title:", title);
        if (context.length) {
          const link = document.createElement('a');
          var markdownBlob = new Blob([context], { type: 'text/markdown' });
          link.href = URL.createObjectURL(markdownBlob);
          link.download = `${title}.md`; 
          link.click();
          URL.revokeObjectURL(link.href);
        } else {
          console.log("context empty");
        }
      },
      onerror: function (err) {
        console.error("请求失败:", err);
      }
    });
  }
})();