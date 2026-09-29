document.querySelectorAll("[data-password-toggle]").forEach((button) => {
  button.addEventListener("click", () => {
    const inputId = button.dataset.passwordToggle;

    const input = document.getElementById(inputId);

    if (!input) {
      return;
    }

    if (input.type === "password") {
      input.type = "text";
    } else {
      input.type = "password";
    }
  });
});