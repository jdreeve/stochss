let app = require('../app');
var $ = require('jquery');
var xhr = require('xhr');
var path = require('path');
//views
var View = require('ampersand-view');
//templates
var template = require('../templates/includes/workflowStateButtons.pug');

let modelSaveErrorHtml = (title, error) => {
  return `
    <div id="modelSaveErrorModal" class="modal" tabindex="-1" role="dialog">
      <div class="modal-dialog" role="document">
        <div class="modal-content info">
          <div class="modal-header">
            <h5 class="modal-title"> ${title} </h5>
            <button type="button" class="close" data-dismiss="modal" aria-label="Close">
              <span aria-hidden="true">&times;</span>
            </button>
          </div>
          <div class="modal-body">
            <p> ${error} </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary box-shadow" data-dismiss="modal">Close</button>
          </div>
        </div>
      </div>
    </div>
  `
}

module.exports = View.extend({
  template: template,
  events: {
    'click [data-hook=save]' : 'clickSaveHandler',
    'click [data-hook=start-workflow]'  : 'clickStartWorkflowHandler',
    'click [data-hook=edit-model]' : 'clickEditModelHandler',
  },
  initialize: function (attrs, options) {
    View.prototype.initialize.apply(this, arguments);
  },
  render: function () {
    View.prototype.render.apply(this, arguments);
  },
  clickSaveHandler: function (e) {
    this.saving();
    var self = this;
    var model = this.model
    var wkflType = this.parent.parent.type;
    var optType = document.URL.endsWith(".mdl") ? "sn" : "se";
    var workflow = document.URL.endsWith(".mdl") ? this.parent.parent.workflowName : this.parent.parent.wkflDirectory
    this.saveModel(function () {
      var endpoint = path.join(app.getApiPath(), 'workflow/save-workflow/', wkflType, optType, model.directory, "<--GillesPy2Workflow-->", workflow);
      xhr({uri: endpoint}, function (err, response, body) {
        self.saved();
        if(document.URL.endsWith('.mdl')){
          setTimeout(function () {
            var dirname = window.location.pathname.split('/')
            dirname.pop()
            dirname = dirname.join('/')
            window.location.href = path.join(dirname, self.parent.parent.workflowName + '.wkfl')
          }, 3000); 
        }
      });
    });
  },
  clickStartWorkflowHandler: function (e) {
    this.saveModel(this.runWorkflow.bind(this));
  },
  clickEditModelHandler: function (e) {
    var self = this
    this.saveModel(function () {
      window.location.href = path.join(app.getBasePath(), "stochss/models/edit", self.model.directory);
    });
  },
  saveModel: function (cb) {
    // this.model is a ModelVersion, the parent of the collection is Model
    let self = this
    if(this.model.simulationSettings.isAutomatic){
      this.model.simulationSettings.letUsChooseForYou();
    }
    var model = this.model;
    if (cb) {
      model.save(model.attributes, {
        success: cb,
        error: function (model, response, options) {
          console.error("Error saving model:", model);
          console.error("Response:", response);
          self.saveError()
          let title = response.body.Reason
          let error = response.body.Message
          var saveErrorModal = $(modelSaveErrorHtml(title, error)).modal()
        },
      });
    } else {
      model.saveModel();
    }
  },
  saving: function () {
    var saving = this.queryByHook('saving-workflow');
    var saved = this.queryByHook('saved-workflow');
    var saveError = this.queryByHook('save-error');
    saved.style.display = "none";
    saveError.style.display = "none";
    saving.style.display = "inline-block";
  },
  saved: function () {
    var saving = this.queryByHook('saving-workflow');
    var saved = this.queryByHook('saved-workflow');
    saving.style.display = "none";
    saved.style.display = "inline-block";
  },
  saveError: function () {
    var saving = this.queryByHook('saving-workflow');
    var saveError = this.queryByHook('save-error');
    saving.style.display = "none";
    saveError.style.display = "inline-block";
  },
  runWorkflow: function () {
    var model = this.model;
    var wkflType = this.parent.parent.type;
    var optType = document.URL.endsWith(".mdl") ? "rn" : "re";
    var workflow = document.URL.endsWith(".mdl") ? this.parent.parent.workflowName : this.parent.parent.wkflDirectory
    var endpoint = path.join(app.getApiPath(), '/workflow/run-workflow/', wkflType, optType, model.directory, "<--GillesPy2Workflow-->", workflow);
    var self = this;
    xhr({ uri: endpoint },function (err, response, body) {
      self.parent.collapseContainer();
      if(document.URL.endsWith('.mdl')){
        setTimeout(function () {
          let pathname = window.location.pathname.split('/');
          pathname.pop()
          pathname = pathname.join('/')
          workflowpath = path.join(pathname, self.parent.parent.workflowName + '.wkfl')
          window.location.href = workflowpath;
        }, 3000);        
      }else{
        self.parent.parent.updateWorkflowStatus();
      }
    });
  },
});
