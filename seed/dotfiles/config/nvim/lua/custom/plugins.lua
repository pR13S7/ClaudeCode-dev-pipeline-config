local plugins = {
  {
    "neovim/nvim-lspconfig",
    config = function()
      require "plugins.configs.lspconfig"
      require "custom.configs.lspconfig"
    end,
  },
  {
   "williamboman/mason.nvim",
   opts = {
      ensure_installed = {
        "lua-language-server",
        "html-lsp",
        "stylua",
        "pyright",
        "typescript-language-server",
        "biome",
        "gopls",
        "emmet_ls"
      },
    },
  }
}

return  plugins
