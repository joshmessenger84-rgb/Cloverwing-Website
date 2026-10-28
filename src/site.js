// Cloverwing Studio: two small behaviours, nothing else.
(function () {
  // 1. Book page: switch between front cover, back cover and inside pages.
  var thumbs = document.querySelectorAll('[data-view]');
  thumbs.forEach(function (btn) {
    btn.addEventListener('click', function () {
      thumbs.forEach(function (b) { b.setAttribute('aria-pressed', String(b === btn)); });
      document.querySelectorAll('[data-pane]').forEach(function (p) {
        p.hidden = p.getAttribute('data-pane') !== btn.getAttribute('data-view');
      });
    });
  });

  // 2. Workbooks page: filter the shelf by age and subject.
  var shelf = document.querySelector('[data-filter-shelf]');
  if (!shelf) return;
  var state = { age: 'all', topic: 'all' };
  var books = shelf.querySelectorAll('.book');
  var empty = document.getElementById('no-match');

  function apply() {
    var shown = 0;
    books.forEach(function (b) {
      var ok = (state.age === 'all' || b.dataset.age === state.age) &&
               (state.topic === 'all' || b.dataset.topic === state.topic);
      b.hidden = !ok;
      if (ok) shown++;
    });
    if (empty) empty.hidden = shown > 0;
    document.querySelectorAll('[data-filter]').forEach(function (c) {
      c.setAttribute('aria-pressed', String(state[c.dataset.filter] === c.dataset.value));
    });
  }
  document.querySelectorAll('[data-filter]').forEach(function (c) {
    c.addEventListener('click', function () {
      state[c.dataset.filter] = c.dataset.value;
      apply();
    });
  });
  // workbooks.html#birds opens with that subject already chosen
  var hash = (location.hash || '').slice(1);
  if (hash && shelf.querySelector('[data-topic="' + hash.replace(/[^a-z0-9-]/g, '') + '"]')) state.topic = hash;
  apply();
})();
