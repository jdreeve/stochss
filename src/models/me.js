var path = require('path');
var app = require('ampersand-app');
var Model = require('ampersand-model');

module.exports = Model.extend({
  url: path.resolve(app.config.apiUrl, 'user'),
  props: {
    name: 'string'
  }
})
