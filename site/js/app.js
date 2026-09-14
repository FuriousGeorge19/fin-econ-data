import { mount } from './lib/card.js';
import { todayET } from './lib/dates.js';

const pageEl = document.querySelector('script#page');
const { blocks } = JSON.parse(pageEl.textContent);
const today = todayET();

blocks.forEach(block => mount(block, today));
