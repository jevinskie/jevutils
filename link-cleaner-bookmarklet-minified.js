function a(a,e=!1,s=!1,r=localStorage["amazon-tracking-id"]){try{var c=new URL(a)}catch(e){if(e instanceof TypeError)c=new URL(a.split(/"(?:[^\\"]|\\.)*"/)[1].trim())}if(console.log("Old link:",c),"l.facebook.com"===c.host&&c.searchParams.has("u")){var h=decodeURI(c.searchParams.get("u"));c=new URL(h)}else if("href.li"===c.host){var t=c.href.split("?")[1];c=new URL(t)}else"www.google.com"===c.host&&"/url"===c.pathname&&c.searchParams.has("url")&&(c=new URL(c.searchParams.get("url")));var o=new URL(c.origin+c.pathname);if(c.searchParams.has("q")&&o.searchParams.append("q",c.searchParams.get("q")),c.host.includes("play.google.com")&&c.searchParams.has("id")&&o.searchParams.append("id",c.searchParams.get("id")),c.host.includes("macys.com")&&c.searchParams.has("ID")&&o.searchParams.append("ID",c.searchParams.get("ID")),c.host.includes("youtube.com")&&c.searchParams.has("v")){if(c.searchParams.has("v")&&e){var n=/^.*(youtu\.be\/|embed\/|shorts\/|\?v=|\&v=)(?<videoID>[^#\&\?]*).*/.exec(c.href).groups.videoID;o=new URL("https://youtu.be/"+n)}else c.searchParams.has("v")&&o.searchParams.append("v",c.searchParams.get("v"));c.searchParams.has("t")&&o.searchParams.append("t",c.searchParams.get("t"))}else c.host.includes("youtube.com")&&c.pathname.includes("playlist")&&c.searchParams.has("list")&&o.searchParams.append("list",c.searchParams.get("list"));if(c.host.includes("facebook.com")&&c.pathname.includes("story.php")&&(o.searchParams.append("story_fbid",c.searchParams.get("story_fbid")),o.searchParams.append("id",c.searchParams.get("id"))),c.host.includes("amazon")&&(c.pathname.includes("/dp/")||c.pathname.includes("/product/"))){o.hostname=o.hostname.replace("www.","");var m=/(?:\/dp\/|\/product\/)(\w*|\d*)/g.exec(c.pathname)[1];m&&(o.pathname="/dp/"+m)}return(c.host.includes("twitter.com")||c.host.includes("x.com"))&&s&&(o.host="fxtwitter.com"),c.host.includes("amazon")&&r&&o.searchParams.append("tag",r),c.host.includes("lenovo.com")&&c.searchParams.has("bundleId")&&o.searchParams.append("bundleId",c.searchParams.get("bundleId")),console.log("New link:",o),o.toString()}window.location.href=a(window.location.href,!0,!0);