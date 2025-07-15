// eslint-disable-next-line import/no-anonymous-default-export
export default {
  index: {
    title: "Getting Start",
    theme: {
      // breadcrumb: false,
      // toc: false,
      // layout: "full",
      // typesetting: "article",
    },
  },

  about: { title: "About This Project", type: "page" },
  contact: {
    title: "Contact Us",
    // display: "hidden",
  },
  guides: { title: "Guides" },
  github: {
    title: "GitHub",
    href: "https://github.com",
    newWindow: true,
  },
  resources: {
    title: "Resources",
    type: "menu",
    items: {
      github: {
        title: "GitHub",
        href: "https://github.com",
      },
      contact: {
        title: "Contact Us",
        href: "mailto:hi@example.com",
      },
    },
  },
};
