//models
var State = require('ampersand-state');

module.exports = State.extend({
  props: {
    seed: {
      type: 'number',
      default: -1,
    },
  },
  initialize: function (attrs, options) {
    State.prototype.initialize.apply(this, arguments);
  },
});