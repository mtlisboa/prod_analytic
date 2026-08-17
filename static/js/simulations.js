(function () {
  var list = document.getElementById('interval-list');
  var addButton = document.getElementById('add-interval');
  var template = document.getElementById('empty-interval');
  var total = document.getElementById('id_intervals-TOTAL_FORMS');
  if (!list || !addButton || !template || !total) return;

  function refreshNumbers() {
    list.querySelectorAll('[data-interval-form]').forEach(function (row, index) {
      row.querySelector('.interval-number').textContent = String(index + 1).padStart(2, '0');
      var position = row.querySelector('input[name$="-position"]');
      if (position) position.value = index + 1;
    });
  }

  addButton.addEventListener('click', function () {
    var index = Number(total.value);
    list.insertAdjacentHTML('beforeend', template.innerHTML.replaceAll('__prefix__', index));
    total.value = index + 1;
    refreshNumbers();
  });

  list.addEventListener('click', function (event) {
    var button = event.target.closest('.remove-interval');
    if (!button) return;
    var row = button.closest('[data-interval-form]');
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

  refreshNumbers();
}());
