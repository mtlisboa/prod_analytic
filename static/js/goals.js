(function () {
  var list = document.getElementById('subject-list');
  var addButton = document.getElementById('add-subject');
  var template = document.getElementById('empty-subject');
  var total = document.getElementById('id_subjects-TOTAL_FORMS');
  if (!list || !addButton || !template || !total) return;

  function refreshNumbers() {
    list.querySelectorAll('[data-subject-form]:not([hidden])').forEach(function (row, index) {
      row.querySelector('.subject-number').textContent = String(index + 1).padStart(2, '0');
      var position = row.querySelector('input[name$="-position"]');
      if (position) position.value = index + 1;
    });
  }

  function sanitizeSubjectInput(input) {
    input.value = input.value.normalize('NFD').replace(/[\u0300-\u036f]/g, '').toUpperCase().replace(/[^A-Z0-9 ]/g, '').replace(/\s+/g, ' ').trimStart();
  }

  function addSubject() {
    var index = Number(total.value);
    list.insertAdjacentHTML('beforeend', template.innerHTML.replaceAll('__prefix__', index));
    total.value = index + 1;
    refreshNumbers();
  }

  addButton.addEventListener('click', addSubject);
  list.addEventListener('click', function (event) {
    var button = event.target.closest('.remove-subject');
    if (!button) return;
    var row = button.closest('[data-subject-form]');
    var deleteInput = row.querySelector('input[name$="-DELETE"]');
    var idInput = row.querySelector('input[name$="-id"]');
    if (idInput && idInput.value) {
      deleteInput.checked = true;
      row.hidden = true;
    } else {
      row.remove();
    }
    refreshNumbers();
  });
  list.addEventListener('input', function (event) {
    if (event.target.matches('[data-uppercase-subject]')) sanitizeSubjectInput(event.target);
  });

  if (!list.querySelector('[data-subject-form]')) addSubject();
  refreshNumbers();
}());
