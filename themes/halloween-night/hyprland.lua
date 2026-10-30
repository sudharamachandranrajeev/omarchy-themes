-- Halloween Night: jack-o'-lantern orange fading to witch violet on the
-- focused window, a faint ember glow behind it, and dusk-violet when idle.
-- Only colours and shadows change; gaps, input and bindings stay yours.
local active_border_color = { colors = { "rgba(ff7a1aee)", "rgba(b44dffee)" }, angle = 45 }
local inactive_border_color = "rgba(3b2752aa)"
local active_shadow_color = "rgba(ff7a1a40)"
local inactive_shadow_color = "rgba(0a071066)"

hl.config({
  general = {
    col = {
      active_border = active_border_color,
      inactive_border = inactive_border_color,
    },
  },

  group = {
    col = {
      border_active = active_border_color,
      border_inactive = inactive_border_color,
    },
  },

  decoration = {
    shadow = {
      enabled = true,
      range = 12,
      render_power = 3,
      color = active_shadow_color,
      color_inactive = inactive_shadow_color,
    },
  },
})
