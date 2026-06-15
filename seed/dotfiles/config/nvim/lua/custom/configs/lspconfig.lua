local config = require("plugins.configs.lspconfig")

local on_attach = config.on_attach
local capabilities = config.capabilities

---@diagnostic disable-next-line: different-requires
local lspconfig = require("lspconfig")

local servers = { "html", "cssls", "clangd", "elixirls", "gopls", "pyright", "tailwindcss", "phpactor", "tsserver", "emmet_ls", "biome"}
for _, lsp in ipairs(servers) do
  lspconfig[lsp].setup {
    on_attach = on_attach,
    capabilities = capabilities,
  }
end

-- configure emmet language server
lspconfig["emmet_ls"].setup({
	capabilities = capabilities,
	on_attach = on_attach,
	filetypes = { "html", "typescriptreact", "javascriptreact", "css", "sass", "scss", "less", "svelte", "php", "template" },
})


