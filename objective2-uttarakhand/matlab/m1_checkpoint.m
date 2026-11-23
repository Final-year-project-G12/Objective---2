function m1_checkpoint(root)
% M1_CHECKPOINT  MATLAB checkpoint M1 of the Unified Rebuild Plan (section 0.2, rule R18), Uttarakhand, common 100 L plant.
%
%   m1_checkpoint('D:\Objective---2\objective2-uttarakhand')
%
% Shows the FROZEN Objective 2 simulations with no learned controller (always-charge B0 only; the safety shield acts inside the kernel):
% the water-only tank (the installed design in every regime) against the PCM designs taken to the one-shot test, on the same real days,
% with water temperature, PCM temperature and liquid fraction, heat exchanged with the PCM, and the energy balance.
%
% Input: results/m1_matlab/hourly_r<c>_<case>.csv and summary.csv, written by scripts/m1_export.py from the O2 multi-node kernel
% (select year 2021, 37.5 s, centre anchor). MATLAB does NOT re-simulate the tank; it recomputes every checked number from the hourly
% records alone and compares it with the kernel's own summary.
%
% Gate (plan M1): the MATLAB numbers match the O2 node-model numbers
%   (1) annual useful energy, annual and 18:00-09:00 window delivery at 45 C: relative difference <= 1e-9
%   (2) energy balance closed from the hourly flows: |dE_stored - (Q_coll - Q_load - Q_loss)| / Q_coll <= 1e-6 %
%   (3) ranking of the designs by window delivery identical to the kernel's ranking in every regime
% Writes results/m1_matlab/m1_gate.csv, m1_gate.txt and figures/*.png.

if nargin < 1, root = fileparts(fileparts(mfilename('fullpath'))); end
set(groot, 'defaultTextInterpreter', 'none', 'defaultAxesTickLabelInterpreter', 'none', 'defaultLegendInterpreter', 'none');
d   = fullfile(root, 'results', 'm1_matlab');
fig = fullfile(d, 'figures');
if ~exist(fig, 'dir'), mkdir(fig); end
S = readtable(fullfile(d, 'summary.csv'), 'TextType', 'string', 'VariableNamingRule', 'preserve');
S = renamevars(S, 'case', 'design');      % 'case' is a MATLAB keyword
winHours = [18:23, 0:8];

rows = {};
for i = 1:height(S)
    H = readtable(fullfile(d, sprintf('hourly_r%d_%s.csv', S.regime(i), S.design(i))), 'TextType', 'string');
    useful = sum(H.Q_load_Wh) / 1000;
    edel   = sum(H.Edel_target_Wh) / 1000;
    win    = sum(H.Edel_target_Wh(ismember(H.hour_of_day, winHours))) / 1000;
    qc     = sum(H.Q_collector_Wh) / 1000;
    flows  = qc - sum(H.Q_load_net_Wh) / 1000 - sum(H.Q_loss_Wh) / 1000;
    dE     = H.E_stored_kWh(end) - S.E_stored_initial_kWh(i);
    closure = abs(dE - flows) / qc * 100;
    rows(end+1, :) = {S.regime(i), S.design(i), S.useful_kWh(i), useful, S.E_del45_annual_kWh(i), edel, ...
                      S.E_del45_window_kWh(i), win, S.residual_pct(i), closure}; %#ok<AGROW>
end
G = cell2table(rows, 'VariableNames', {'regime','design','useful_py','useful_ml','edel_py','edel_ml','window_py','window_ml', ...
                                      'closure_py_pct','closure_ml_pct'});
rel = @(a, b) abs(a - b) ./ max(abs(a), 1e-12);
G.max_rel_diff = max([rel(G.useful_py, G.useful_ml), rel(G.edel_py, G.edel_ml), rel(G.window_py, G.window_ml)], [], 2);
G.numbers_match = G.max_rel_diff <= 1e-9;
G.balance_closed = G.closure_ml_pct <= 1e-6;
G.rank_py = zeros(height(G), 1); G.rank_ml = zeros(height(G), 1);
for r = unique(G.regime)'
    k = find(G.regime == r);
    [~, o] = sort(G.window_py(k), 'descend'); G.rank_py(k(o)) = 1:numel(k);
    [~, o] = sort(G.window_ml(k), 'descend'); G.rank_ml(k(o)) = 1:numel(k);
end
G.rank_match = G.rank_py == G.rank_ml;
writetable(G, fullfile(d, 'm1_gate.csv'));
pass = all(G.numbers_match) && all(G.balance_closed) && all(G.rank_match);
fid = fopen(fullfile(d, 'm1_gate.txt'), 'w');
fprintf(fid, 'M1 gate (plan section 0.2): %s\n', ternary(pass, 'PASS', 'FAIL'));
fprintf(fid, 'runs %d | numbers match %d | balance closed %d | ranking identical %d\n', height(G), sum(G.numbers_match), ...
        sum(G.balance_closed), sum(G.rank_match));
fprintf(fid, 'largest relative difference %.3g | largest MATLAB closure %.3g %%\n', max(G.max_rel_diff), max(G.closure_ml_pct));
fprintf(fid, 'MATLAB %s\n', version);
fclose(fid);
type(fullfile(d, 'm1_gate.txt'));

% ---------------------------------------------------------------- figures
cols = lines(4);
for r = unique(S.regime)'
    k = find(S.regime == r);
    T = cell(numel(k), 1);
    for j = 1:numel(k), T{j} = readtable(fullfile(d, sprintf('hourly_r%d_%s.csv', r, S.design(k(j)))), 'TextType', 'string'); end
    W = T{S.design(k) == "water_only"}; P = T{S.design(k) == "pick"}; pickPcm = S.pcm(k(S.design(k) == "pick"));
    daily = groupsummary(table(W.local_date, W.I_t_Wm2, 'VariableNames', {'day','I'}), 'day', 'sum', 'I');
    [~, iClear] = max(daily.sum_I);
    q = sort(daily.sum_I); iCloud = find(daily.sum_I == q(max(1, round(0.1 * numel(q)))), 1);
    days = {daily.day(iClear), 'clearest day'; daily.day(iCloud), '10th-percentile irradiation day'};

    f = figure('Visible', 'off', 'Position', [50 50 1500 900]); lightTheme(f);
    tl = tiledlayout(f, 4, 2, 'TileSpacing', 'compact');
    for c = 1:2
        i0 = find(W.local_date == days{c, 1}, 1) + 5;                       % from 05:00 local, 36 h
        idx = i0:min(i0 + 35, height(W)); t = 0:numel(idx) - 1;
        nexttile(tl, c);
        plot(t, W.T_w_C(idx), '-', 'Color', cols(1,:), 'LineWidth', 1.6); hold on
        plot(t, W.T_bottom_C(idx), ':', 'Color', cols(1,:), 'LineWidth', 1.2);
        plot(t, P.T_w_C(idx), '-', 'Color', cols(2,:), 'LineWidth', 1.6);
        plot(t, P.T_bottom_C(idx), ':', 'Color', cols(2,:), 'LineWidth', 1.2);
        yline(45, 'k--'); yline(72, 'r:');
        ylabel('water temperature (C)'); title(sprintf('%s %s: top (solid) / bottom (dotted)', days{c, 2}, days{c, 1}));
        legend({'water-only top', 'water-only bottom', 'PCM top', 'PCM bottom', '45 C', 'guard 72 C'}, 'Location', 'best', 'FontSize', 7);
        nexttile(tl, c + 2);
        yyaxis left; plot(t, P.T_pcm_C(idx), 'LineWidth', 1.4); ylabel('PCM temperature (C)');
        yyaxis right; plot(t, P.f_melt(idx), 'LineWidth', 1.4); ylabel('liquid fraction'); ylim([0 1]);
        title(sprintf('PCM design (%s): temperature and liquid fraction', pickPcm));
        nexttile(tl, c + 4);
        bar(t, P.Q_pcm_Wh(idx), 'FaceColor', cols(3,:)); ylabel('Wh per hour');
        title('heat exchanged with the PCM (+ = PCM charging, - = PCM heats the water)');
        nexttile(tl, c + 6);
        plot(t, W.I_t_Wm2(idx), 'k'); ylabel('irradiance (W/m2)'); yyaxis right; bar(t, W.draw_kg(idx), 'FaceAlpha', .4);
        ylabel('draw (kg/h)'); xlabel('hours from 05:00 local');
    end
    title(tl, sprintf('M1 checkpoint, regime %d, 2021, always-charge B0 (O2 kernel, 37.5 s, centre anchor)', r));
    exportgraphics(f, fullfile(fig, sprintf('m1_r%d_days.png', r)), 'Resolution', 130); close(f);

    f = figure('Visible', 'off', 'Position', [50 50 1300 450]); lightTheme(f);
    tl = tiledlayout(f, 1, 2, 'TileSpacing', 'compact');
    nexttile(tl);
    E = zeros(numel(k), 4);
    for j = 1:numel(k)
        H = T{j};
        E(j, :) = [sum(H.Q_collector_Wh), -sum(H.Q_load_net_Wh), -sum(H.Q_loss_Wh), ...
                   -(H.E_stored_kWh(end) - S.E_stored_initial_kWh(k(j))) * 1000] / 1000;
    end
    bar(categorical(S.design(k)), E, 'stacked'); ylabel('kWh / year');
    legend({'collector in', 'delivered (out)', 'tank loss (out)', '- change in stored'}, 'Location', 'southoutside', 'Orientation', 'horizontal');
    title('Annual energy balance (closes to < 1e-6 %)');
    nexttile(tl);
    gk = G(G.regime == r, :);
    bar(categorical(gk.design), gk.window_ml - gk.window_ml(gk.design == "water_only"));
    ylabel('window delivery minus water-only (kWh/yr)'); yline(0, 'k');
    title('Window delivery (18-09 h, 45 C) minus water-only');
    title(tl, sprintf('M1 checkpoint, regime %d: energy balance and ranking', r));
    exportgraphics(f, fullfile(fig, sprintf('m1_r%d_balance.png', r)), 'Resolution', 130); close(f);
end
end

function out = ternary(c, a, b)
if c, out = a; else, out = b; end
end

function lightTheme(f)
% report figures on a light background (R2025a+ defaults to the desktop theme)
try, theme(f, 'light'); catch, set(f, 'Color', 'w'); end
end
