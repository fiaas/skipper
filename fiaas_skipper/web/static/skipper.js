function getStatus() {
  $.ajax({
    type: "GET",
    url: "/api/status",
    success: function(data) {
      var json = $.parseJSON(data);
      var statusmap = {
       "OK": "success",
       "UNKNOWN": "warning",
       "UNAVAILABLE": "warning",
       "ERROR": "danger",
       "FAILED": "danger",
       "VERSION_MISMATCH": "warning"
      };
      $("#tbody").empty();
      $.each(json, function (index, item) {
           var eachrow = "<tr class=\"" + statusmap[item.status] + "\">"
                       + "<th scope=\"row\">" + item.namespace + "</td>"
                       + "<td>" + item.status.replace(/_/g, " ") + "</td>"
                       + "<td>" + [item.description].join('') + "</td>"
                       + "<td>" + item.channel + "</td>"
                       + "<td>" + item.version + "</td>"
                       + "<td><button class=\"btn btn-primary btn-block btnDeploy\" type=\"submit\" data-namespace=\"" + item.namespace + "\">Deploy</button></td>"
                       + "</tr>";
           $('#tbody').append(eachrow);
       });
       $(".btnDeploy").each(function(){
           var $this = $(this);
           $this.click(function(){
               $.ajax({
                   type: "POST",
                   contentType: "application/json",
                   url: "/api/deploy",
                   data: "{\"namespaces\": [\"" + $(this).data('namespace') + "\"]}",
                   success: function(data) {
                       alert("Deployment to " + $this.data("namespace") + " scheduled successfully");
                   }
               });
               getStatus(); // refresh
           });
       });
    }
  });
  window.setTimeout(function() { getStatus(); }, 5000);
}

function onStatusPageLoad() {
  getStatus();
}

function onDeployPageLoad() {
  $("#btnSubmit").click(function(){
    $.ajax({
      type: "POST",
      url: "/api/deploy",
      success: function(data) {
        alert("Deployment scheduled successfully");
      }
    });
  });
}

$().ready(function() {
  if ($("body").attr("class") === "deploy") {
    onDeployPageLoad();
  } else if ($("body").attr("class") === "status") {
    onStatusPageLoad();
  }
});
