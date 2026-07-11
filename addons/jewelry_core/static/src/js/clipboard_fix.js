// Polyfill for navigator.clipboard.writeText for older browsers/insecure contexts.
// Some Odoo backend features rely on clipboard API; this fallback uses the
// legacy document.execCommand('copy') method when the modern API isn't available.
if (!navigator.clipboard) {
    navigator.clipboard = {};
}
if (!navigator.clipboard.writeText) {
    navigator.clipboard.writeText = function (text) {
        return new Promise(function (resolve, reject) {
            try {
                var ta = document.createElement('textarea');
                ta.value = text;
                ta.style.position = 'fixed';
                ta.style.opacity = '0';
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
                resolve();
            } catch (e) {
                reject(e);
            }
        });
    };
}
