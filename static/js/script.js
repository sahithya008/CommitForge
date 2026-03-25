document.addEventListener("DOMContentLoaded", function () {
    const toggle = document.getElementById("menuToggle");
    const sidebar = document.getElementById("sidebar");
    const overlay = document.getElementById("sidebarOverlay");

    const isMobile = () => window.matchMedia("(max-width: 768px)").matches;

    const openSidebar = () => {
        if (sidebar) sidebar.classList.add("open");
        if (overlay) overlay.style.display = "block";
    };

    const closeSidebar = () => {
        if (sidebar) sidebar.classList.remove("open");
        if (overlay) overlay.style.display = "none";
    };

    if (toggle) {
        toggle.addEventListener("click", function () {
            if (!sidebar) return;
            if (sidebar.classList.contains("open")) {
                closeSidebar();
            } else {
                openSidebar();
            }
        });
    }

    if (overlay) {
        overlay.addEventListener("click", closeSidebar);
    }

    const resizeHandler = () => {
        if (!isMobile() && sidebar) {
            sidebar.classList.remove("open");
            if (overlay) overlay.style.display = "none";
        }
    };

    window.addEventListener("resize", resizeHandler);
    resizeHandler();

    const navLinks = document.querySelectorAll(".nav-link");
    navLinks.forEach((link) => {
        if (link.href === window.location.href) {
            link.classList.add("active");
        }
    });
});
