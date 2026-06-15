local M = {}

M.custom ={
  n ={
    -- clear search highlights
    ["<leader>nh"] = {":nohl<CR>"},
    -- select all
    ["<C-a>"] = {"ggVG"},
    -- delete W/O copying
    ["<leader>d"] = {'"_d'}
  }
}

return M
