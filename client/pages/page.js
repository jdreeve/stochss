let PageView = require('./base');
let MainView = require('../views/main');
//var templates = require('../templates');
let template = require('../templates/pages/home.pug');
let domReady = require('domready');

let $ = require('jquery');
let bootstrap = require('bootstrap');

let app = require('../app');

import styles from '../styles/styles.css';
import bootstrapStyles from '../styles/bootstrap.css';

export default function initPage (page) {
  domReady(() => {
    let mainView = new MainView({
      el: document.body
    });
    let p = new page({
      el: document.querySelector('[data-hook="page-container"]'),
    });
    p.render()
  })
}