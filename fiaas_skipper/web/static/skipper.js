
// Copyright 2017-2019 The FIAAS Authors
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//      http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

function getStatus() {
  $.ajax({
    type: "GET",
    url: "/api/status",
    success: function(data) {
      var json = data;
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
                       + "<td><button class=\"btn btn-primary btn-block btnDeploy\" type=\"submit\" data-namespace=\"" + item.namespace + "\" data-toggle=\"modal\" data-target=\"#deployModal\">Deploy</button></td>"
                       + "</tr>";
           $('#tbody').append(eachrow);
       });
    }
  });
  window.setTimeout(function() { getStatus(); }, 5000);
}

function onStatusPageLoad() {
    $("#deployModal").find(".btn-primary").click(function() {
        var forceBootstrap = $("#deployModal").find("#force-bootstrap").is(":checked");
        var namespace = $("#deployModal").find("#namespace").val();
        $.ajax({
            type: "POST",
            contentType: "application/json",
            url: "/api/deploy",
            data: "{\"namespaces\": [\"" + namespace + "\"], \"force_bootstrap\": " + (forceBootstrap ? "true" : "false") + "}",
            success: function(data) {
                $("#deployModal").modal("hide");
            }
        });
    });
    $("#deployModal").on("show.bs.modal", function (event) {
        var button = $(event.relatedTarget);
        var namespace = button.data("namespace");
        var modal = $(this);
        modal.find(".modal-title").text("Deploy fiaas-deploy-daemon to namespace: " + namespace + "?");
        modal.find(".modal-body input").val(namespace);
    });
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
