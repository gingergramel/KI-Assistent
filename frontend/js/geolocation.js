function getStandort() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject("Geolocation wird von diesem Browser nicht unterstützt.");
      return;
    }

    navigator.geolocation.getCurrentPosition(
      (position) => {
        resolve({
          lat: position.coords.latitude,
          lon: position.coords.longitude
        });
      },
      (error) => {
        reject("Standort konnte nicht ermittelt werden: " + error.message);
      }
    );
  });
}