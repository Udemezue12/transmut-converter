function goBack() {
  if (window.history.length > 1) {
    window.history.back();

    
    setTimeout(() => {
      window.location.href = "/";
    }, 500);
  } else {
    window.location.href = "/";
  }
}