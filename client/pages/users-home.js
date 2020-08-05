let $ = require('jquery');
let xhr = require('xhr');
let path = require('path');
//support files
let app = require('../app');
let modals = require('../modals');
//views
let PageView = require('./base');
//templates
let template = require('../templates/pages/usersHome.pug');

import initPage from './page.js';

let usersHomePage = PageView.extend({
  template: template,
  events: {
    'click [data-hook=new-model-btn]' : 'handleNewModelClick',
    'click [data-hook=new-project-btn]' : 'handleNewProjectClick',
    'click [data-hook=browse-projects-btn]' : 'handleBrowseProjectsClick',
    'click [data-hook=browse-files-btn]' : 'handleBrowseFilesClick',
    'click [data-hook=quickstart-btn]' : 'handleQuickstartClick'
  },
  handleNewModelClick: function (e) {
    let self = this
    if(document.querySelector("#newModalModel")) {
      document.querySelector("#newModalModel").remove()
    }
    let modal = $(modals.renderCreateModalHtml(true, false)).modal()
    let okBtn = document.querySelector("#newModalModel .ok-model-btn")
    let input = document.querySelector("#newModalModel #modelNameInput")
    input.focus()
    input.addEventListener("keyup", function (event) {
      if(event.keyCode === 13){
        event.preventDefault();
        okBtn.click();
      }
    });
    okBtn.addEventListener("click", function (e) {
      if(Boolean(input.value)){
        modal.modal('hide')
        let modelPath = input.value + '.mdl'
        let queryString = "?path="+modelPath+"&message=''"
        let endpoint = path.join(app.getBasePath(), "stochss/models/edit")+queryString
        self.navToPage(endpoint)
      }
    });
  },
  handleNewProjectClick: function (e) {
    let self = this
    if(document.querySelector("#newProjectModal")) {
      document.querySelector("#newProjectModal").remove()
    }
    let modal = $(modals.newProjectModalHtml()).modal()
    let okBtn = document.querySelector("#newProjectModal .ok-model-btn")
    let input = document.querySelector("#newProjectModal #projectNameInput")
    input.focus()
    input.addEventListener("keyup", function (event) {
      if(event.keyCode === 13){
        event.preventDefault();
        okBtn.click();
      }
    });
    okBtn.addEventListener("click", function (e) {
      if(Boolean(input.value)) {
        modal.modal('hide')
        let projectPath = input.value + ".proj"
        let queryString = "?path="+projectPath
        let endpoint = path.join(app.getApiPath(), "project/new-project")+queryString
        xhr({uri:endpoint, json:true}, function (err, response, body) {
          if(response.statusCode < 400) {
            let projectQS = "?path="+body.path
            let projectEP = path.join(app.getBasePath(), "stochss/project/manager")+projectQS
            self.navToPage(projectEP)
          }else{
            let errorModel = $(modals.newProjectOrExperimentErrorHtml(body.Reason, body.Message)).modal()
          }
        });
      }
    });
  },
  handleBrowseProjectsClick: function (e) {
    let endpoint = path.join(app.getBasePath(), "stochss/project/browser")
    this.navToPage(endpoint)
  },
  handleBrowseFilesClick: function (e) {
    let endpoint = path.join(app.getBasePath(), "stochss/models")
    this.navToPage(endpoint)
  },
  handleQuickstartClick: function (e) {
    let endpoint = path.join(app.getBasePath(), "stochss/quickstart")
    this.navToPage(endpoint)
  },
  navToPage: function (endpoint) {
    window.location.href = endpoint
  }
});

initPage(usersHomePage);