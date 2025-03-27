using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Http;
using Microsoft.Azure.WebJobs;
using Microsoft.Azure.WebJobs.Extensions.Http;
using Microsoft.Extensions.Primitives;
using Newtonsoft.Json; // Use this!!! This is important!!!!!

namespace MyFunctionApp
{
    public static class ForwardFunctions
    {
        // GET function: handles GET requests to /contact.
        // https://secretfunction.azurewebsites.net/dmc/contact
        [FunctionName("ContactFunction")]
        public static async Task<IActionResult> ContactFunction(
            [HttpTrigger(AuthorizationLevel.Anonymous, "get", Route = "contact")] HttpRequest req)
        {
            string baseUrl = "https://<IP or Domain>";
            // Forward GET requests to the team server's GET endpoint.
            string targetUrl = $"{baseUrl}/dmc/contact";
            if (req.QueryString.HasValue)
            {
                targetUrl += req.QueryString.Value;
            }

            HttpClientHandler handler = new HttpClientHandler()
            {
                ServerCertificateCustomValidationCallback = (sender, cert, chain, sslPolicyErrors) => true
            };

            using (HttpClient client = new HttpClient(handler))
            {
                HttpResponseMessage response = await client.GetAsync(targetUrl);
                string responseBody = await response.Content.ReadAsStringAsync();

                // Process the response using Newtonsoft.Json if it is valid JSON.
                try
                {
                    var jsonObj = JsonConvert.DeserializeObject(responseBody);
                    responseBody = JsonConvert.SerializeObject(jsonObj, Formatting.None);
                }
                catch { /* If not valid JSON, return as-is */ }

                return new OkObjectResult(responseBody);
            }
        }

        // POST function: handles POST requests to /resource.
        // https://secretfunction.azurewebsites.net/dmc/resource
        [FunctionName("ResourceFunction")]
        public static async Task<IActionResult> ResourceFunction(
            [HttpTrigger(AuthorizationLevel.Anonymous, "post", Route = "resource")] HttpRequest req)
        {
            string baseUrl = "https://<IP or Domain>";
            // Forward POST requests to the team server's POST endpoint.
            string targetUrl = $"{baseUrl}/dmc/resource";

            string requestBody = await new StreamReader(req.Body).ReadToEndAsync();

            // Process the request body using Newtonsoft.Json (if valid JSON).
            string jsonContent;
            try
            {
                var data = JsonConvert.DeserializeObject(requestBody);
                jsonContent = JsonConvert.SerializeObject(data, Formatting.None);
            }
            catch
            {
                jsonContent = requestBody; // if invalid JSON, use original body.
            }

            HttpClientHandler handler = new HttpClientHandler()
            {
                ServerCertificateCustomValidationCallback = (sender, cert, chain, sslPolicyErrors) => true
            };

            using (HttpClient client = new HttpClient(handler))
            {
                HttpRequestMessage forwardRequest = new HttpRequestMessage(HttpMethod.Post, targetUrl)
                {
                    Content = new StringContent(jsonContent, System.Text.Encoding.UTF8, "application/json")
                };

                // Forward all headers except "Host".
                foreach (var header in req.Headers)
                {
                    if (!header.Key.Equals("Host", StringComparison.OrdinalIgnoreCase))
                    {
                        forwardRequest.Headers.TryAddWithoutValidation(header.Key, header.Value.ToArray());
                    }
                }

                HttpResponseMessage response = await client.SendAsync(forwardRequest);
                string responseBody = await response.Content.ReadAsStringAsync();

                // Process the response using Newtonsoft.Json if it is valid JSON.
                try
                {
                    var responseData = JsonConvert.DeserializeObject(responseBody);
                    responseBody = JsonConvert.SerializeObject(responseData, Formatting.None);
                }
                catch { /* If not valid JSON, return as-is */ }

                return new OkObjectResult(responseBody);
            }
        }
    }
}