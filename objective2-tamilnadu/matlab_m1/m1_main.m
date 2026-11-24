% m1_main.m  -  MATLAB checkpoint M1 (Objective 2, before any DRL agent)
% Shows the Objective 2 tank with its PCM capsules for the SEVEN design criteria of the Fluent study:
%   how the water warms, how the capsules melt, how much heat reaches the water, and how the criteria differ.
% Data come from scripts/c20_m1_export.py (Objective 2 multi-node kernel). This is a VISUALISATION of simulator output:
% not an independent MATLAB re-implementation of the physics, not CFD, not an experiment. Always-charge (B0) is the only control.
%
% Run (from the project root):   matlab -batch "run('matlab_m1/m1_main.m')"                      % regime 0  (folder results/m1)
%                                 M1_DIR=results/m1_regime1 matlab -batch "run('matlab_m1/m1_main.m')"   % regime 1 (export it first:
%                                 python scripts/c20_m1_export.py --regime 1); likewise m1_regime2.
% The folder is taken from the environment variable M1_DIR (an env var, not a workspace variable, because 'clear' below would wipe the latter).
% Outputs: <folder>/figures/*.png, <folder>/figures/*.mp4, <folder>/m1_check.csv

clear; clc;
set(0, 'DefaultFigureVisible', 'off');
root = fileparts(fileparts(mfilename('fullpath')));
m1dir = getenv('M1_DIR'); if isempty(m1dir), m1dir = fullfile('results', 'm1'); end
mdir = fullfile(root, m1dir);
fdir = fullfile(mdir, 'figures'); if ~exist(fdir, 'dir'), mkdir(fdir); end
M = jsondecode(fileread(fullfile(mdir, 'manifest.json')));
crit = M.criteria;  nC = numel(crit);
keys = arrayfun(@(c) string(c.key), crit);
titles = arrayfun(@(c) string(c.title), crit);
kinds = ["clear", "average", "cloudy"];
col = lines(nC);
annual = readtable(fullfile(mdir, 'annual_criteria.csv'));
limits = char(M.limits);
foot = sprintf('Regime %d, PCM %s, 100 L tank, %.1f m^2 collector, %d L/day, always-charge control. Simulator output (not CFD / not experiment).', ...
    M.regime, char(M.pcm), M.plant.collector_area_m2, M.plant.demand_L_day);

%% 1. Fluent-style sealed discharge: water 30 C, capsules 70 C, no sun, no draw (hourly kernel output, 12 h)
D = cell(nC, 1);
for i = 1:nC, D{i} = readtable(fullfile(mdir, sprintf('discharge_%s.csv', keys(i)))); end
fig = figure('Position', [50 50 1500 900]);
subplot(2, 3, 1); hold on;
for i = 1:nC, plot([0; D{i}.hour_index + 1], [30; D{i}.T_w_mean_C], '-o', 'Color', col(i, :), 'LineWidth', 1.4); end
xlabel('time [h]'); ylabel('mean water temperature [C]'); title('Water warms from 30 C'); grid on;
subplot(2, 3, 2); hold on;
for i = 1:nC, plot([0; D{i}.hour_index + 1], [1; D{i}.f_melt], '-o', 'Color', col(i, :), 'LineWidth', 1.4); end
xlabel('time [h]'); ylabel('capsule liquid fraction [-]'); title('Capsules solidify, releasing heat'); grid on; ylim([0 1.05]);
subplot(2, 3, 3); hold on;
for i = 1:nC, plot(D{i}.hour_index + 1, cumsum(D{i}.Q_pcm_Wh) / 1000, '-o', 'Color', col(i, :), 'LineWidth', 1.4); end
xlabel('time [h]'); ylabel('cumulative heat capsules -> water [kWh]'); title('Heat given to the water'); grid on;
subplot(2, 3, 4); hold on;
for i = 1:nC, plot(D{i}.hour_index + 1, D{i}.T_pcm_C, '-o', 'Color', col(i, :), 'LineWidth', 1.4); end
xlabel('time [h]'); ylabel('capsule temperature [C]'); title('Capsule temperature'); grid on;
subplot(2, 3, 5);
fin = cellfun(@(t) t.T_w_mean_C(end), D); bar(fin); set(gca, 'XTick', 1:nC, 'XTickLabel', arrayfun(@(i) sprintf('%d', i - 1), 1:nC, 'UniformOutput', false));
xlabel('criterion'); ylabel('water temperature after 12 h [C]'); title('End of discharge'); grid on;
subplot(2, 3, 6); axis off;
txt = cell(nC + 1, 1); txt{1} = 'criterion  |  N capsules  |  PCM kg  |  dT water 12 h [C]';
for i = 1:nC
    g = M.geometry.(char(keys(i)));
    txt{i + 1} = sprintf('%s | %d | %.1f | %+.2f', titles(i), g.n_capsule, g.pcm_mass_kg, fin(i) - 30);
end
text(0, 1, txt, 'VerticalAlignment', 'top', 'FontName', 'FixedWidth', 'FontSize', 9);
legend(subplot(2, 3, 1), titles, 'Location', 'southeast', 'FontSize', 7);
sgtitle({'Discharge test (Fluent-style): sealed tank, water 30 C, capsules 70 C, no sun, no draw', foot}, 'FontSize', 10);
exportgraphics(fig, fullfile(fdir, 'M1_A_discharge_seven_criteria.png'), 'Resolution', 150); close(fig);

%% 2. Real charging day: how sun, collector and capsules heat the water (three day types)
check = [];
for k = 1:numel(kinds)
    kind = kinds(k);
    P = readtable(fullfile(mdir, sprintf('day_plain_%s.csv', kind)));
    T = cell(nC, 1);
    for i = 1:nC, T{i} = readtable(fullfile(mdir, sprintf('day_%s_%s.csv', keys(i), kind))); end
    h = (0:height(P) - 1)';
    fig = figure('Position', [50 50 1500 1250]);
    tl = tiledlayout(4, 2, 'TileSpacing', 'compact', 'Padding', 'compact');
    nexttile; plot(h, P.I_t_Wm2, 'k', 'LineWidth', 1.3); ylabel('GHI [W/m^2]'); xlabel('hour'); grid on;
    title(sprintf('Sun: %s day (%s), 48 h from local midnight', kind, M.days.(char(kind))));
    nexttile; plot(h, P.T_amb_C, 'r', 'LineWidth', 1.3); ylabel('ambient [C]'); xlabel('hour'); grid on; title('Ambient temperature');
    nexttile; hold on; plot(h, P.T_w_mean_C, 'k', 'LineWidth', 2.2);
    for i = 1:nC, plot(h, T{i}.T_w_mean_C, 'Color', col(i, :), 'LineWidth', 1.1); end
    ylabel('mean water temperature [C]'); xlabel('hour'); title('Water temperature (black = plain tank)'); grid on; yline(45, '--', '45 C delivery');
    legend(["plain"; titles], 'Location', 'eastoutside', 'FontSize', 6);
    nexttile; hold on;
    for i = 1:nC, plot(h, T{i}.f_melt, 'Color', col(i, :), 'LineWidth', 1.1); end
    ylabel('capsule liquid fraction'); xlabel('hour'); title('Capsules melting (day) and freezing (night)'); grid on; ylim([0 1.05]);
    nexttile; hold on; plot(h, P.T_w_max_C - P.T_w_min_C, 'k', 'LineWidth', 2.2);
    for i = 1:nC, plot(h, T{i}.T_w_max_C - T{i}.T_w_min_C, 'Color', col(i, :)); end
    ylabel('top - bottom [C]'); xlabel('hour'); title('Stratification in the tank'); grid on;
    nexttile;
    Ein = zeros(nC + 1, 1); Eload = Ein; Eloss = Ein; Ed = Ein;
    allT = [{P}; T]; nm8all = ["plain tank"; titles];
    for i = 1:nC + 1
        Ein(i) = sum(allT{i}.Q_collector_Wh) / 1000; Eload(i) = sum(allT{i}.Q_load_Wh) / 1000; Eloss(i) = sum(allT{i}.Q_loss_Wh) / 1000;
        Ed(i) = (allT{i}.E_stored_kWh(end) - allT{i}.E_stored_kWh(1));
    end
    bar([Ein Eload Eloss Ed]); set(gca, 'XTick', 1:nC + 1, 'XTickLabel', [{'plain'}, arrayfun(@(i) sprintf('%d', i - 1), 1:nC, 'UniformOutput', false)]);
    legend({'collector in', 'delivered to load', 'tank loss', 'stored change'}, 'FontSize', 7, 'Location', 'northeastoutside'); ylabel('energy over 48 h [kWh]'); title('Heat balance'); grid on;
    nexttile([1 2]); axis off;
    tx = cell(nC + 2, 1); tx{1} = 'case | load kWh | loss kWh | stored dE kWh | balance resid %';
    for i = 1:nC + 1
        resid = (Ein(i) - Eload(i) - Eloss(i) - Ed(i)) / max(Ein(i), 1e-9) * 100;
        nm = nm8all(i);
        tx{i + 1} = sprintf('%s | %.2f | %.2f | %+.2f | %+.2f', nm, Eload(i), Eloss(i), Ed(i), resid);
        check = [check; table(string(kind), nm, Ein(i), Eload(i), Eloss(i), Ed(i), resid, 'VariableNames', {'day', 'case', 'E_collector_kWh', 'E_load_kWh', 'E_loss_kWh', 'dE_stored_kWh', 'balance_resid_pct'})]; %#ok<AGROW>
    end
    text(0, 1, tx, 'VerticalAlignment', 'top', 'FontName', 'FixedWidth', 'FontSize', 9);
    title(tl, {sprintf('Real charging day (%s): how the water warms and how the seven criteria differ', kind), foot}, 'FontSize', 10);
    exportgraphics(fig, fullfile(fdir, sprintf('M1_B_day_%s_seven_criteria.png', kind)), 'Resolution', 150); close(fig);
end
writetable(check, fullfile(mdir, 'm1_check.csv'));

%% 3. Annual ranking of the seven criteria (numbers from the Objective 2 evaluator) and consistency with the MATLAB window ordering
fig = figure('Position', [50 50 1300 600]);
subplot(1, 2, 1); bar(annual.paired_gain_window_kWh); set(gca, 'XTick', 1:nC, 'XTickLabel', arrayfun(@(i) sprintf('%d', i - 1), 1:nC, 'UniformOutput', false));
xlabel('criterion'); ylabel('paired gain vs plain tank [kWh/yr], 45 C window'); title('Delivered energy gain (select year, centre anchor)'); grid on;
subplot(1, 2, 2); bar([annual.shield_h annual.shield_plain_h(1) * ones(nC, 1)]); set(gca, 'XTick', 1:nC, 'XTickLabel', arrayfun(@(i) sprintf('%d', i - 1), 1:nC, 'UniformOutput', false));
legend({'PCM tank', 'plain tank'}); xlabel('criterion'); ylabel('overheat-guard hours per year'); title('Overheat guard hours (PCM tanks are worse: less water)'); grid on;
sgtitle({'Annual comparison of the seven criteria', foot}, 'FontSize', 10);
exportgraphics(fig, fullfile(fdir, 'M1_C_annual_ranking.png'), 'Resolution', 150); close(fig);

%% 4. The four Objective 1 PCMs in the optimal geometry on the same days
names = string(M.four_pcms); tags = arrayfun(@(n) erase(strtok(n, ' '), '-'), names);
fig = figure('Position', [50 50 1500 800]);
for k = 1:numel(kinds)
    subplot(2, 3, k); hold on;
    for j = 1:numel(tags)
        Q = readtable(fullfile(mdir, sprintf('pcm_%s_%s.csv', tags(j), kinds(k)))); plot(0:height(Q) - 1, Q.T_w_mean_C, 'LineWidth', 1.4);
    end
    title(sprintf('Water temperature, %s day', kinds(k))); xlabel('hour'); ylabel('[C]'); grid on;
    subplot(2, 3, 3 + k); hold on;
    for j = 1:numel(tags)
        Q = readtable(fullfile(mdir, sprintf('pcm_%s_%s.csv', tags(j), kinds(k)))); plot(0:height(Q) - 1, Q.f_melt, 'LineWidth', 1.4);
    end
    title('Capsule liquid fraction'); xlabel('hour'); grid on; ylim([0 1.05]);
end
legend(names, 'FontSize', 8, 'Location', 'southeast');
sgtitle({'The four Objective 1 PCMs in the optimal geometry (same weather, same demand)', foot}, 'FontSize', 10);
exportgraphics(fig, fullfile(fdir, 'M1_D_four_pcms.png'), 'Resolution', 150); close(fig);

%% 5. Animated tank cut-away: water colour = node temperature, capsule colour = liquid fraction (plain tank + seven criteria side by side)
cmapT = [0.2 0.4 0.9; 0.3 0.75 0.8; 1 0.7 0.1; 0.9 0.1 0.1];
nOpt = M.geometry.(char(keys(1))).n_capsule; Hd = M.geometry.(char(keys(1))).tank_height_m; Dd = M.geometry.(char(keys(1))).tank_diameter_m;
for k = 1:numel(kinds)
    kind = kinds(k);
    P = readtable(fullfile(mdir, sprintf('day_plain_%s.csv', kind)));
    T = cell(nC, 1); for i = 1:nC, T{i} = readtable(fullfile(mdir, sprintf('day_%s_%s.csv', keys(i), kind))); end
    all8 = [{P}; T]; nm8 = ["Plain tank"; titles];
    vw = VideoWriter(fullfile(fdir, sprintf('M1_E_tank_animation_%s.mp4', kind)), 'MPEG-4'); vw.FrameRate = 6; open(vw);
    fig = figure('Position', [50 50 1700 760], 'Color', 'w');
    nT = height(P);
    hN = cell(nC + 1, 1); hC = cell(nC + 1, 1); hCn = cell(nC + 1, 1); ht = gobjects(nC + 1, 1);
    for i = 1:nC + 1                                              % draw every tank ONCE, update colours per frame
        subplot(2, 4, i); hold on; axis equal; axis([-0.05 Dd + 0.05 -0.05 Hd + 0.05]); axis off;
        hN{i} = gobjects(10, 1);
        for j = 1:10, hN{i}(j) = rectangle('Position', [0, (j - 1) * Hd / 10, Dd, Hd / 10], 'FaceColor', [0.5 0.5 0.5], 'EdgeColor', [0.85 0.85 0.85]); end
        hC{i} = gobjects(0); hCn{i} = [];
        if i > 1
            g = M.geometry.(char(keys(i - 1)));
            drawn = round(g.capsules_per_node * 34 / nOpt);                       % 2-D proxy: drawn count scaled to the optimum (34 drawn = optimum)
            rr = max(0.5 * g.pcm_thickness_m * Dd / 0.399, 0.004);
            for j = 1:10
                nd = drawn(j); if nd <= 0, continue; end
                pos = ((1:nd) - 0.5) / nd * (Dd - 2 * rr) + rr;
                for q = 1:nd
                    hC{i}(end + 1) = rectangle('Position', [pos(q) - rr, (j - 0.5) * Hd / 10 - rr, 2 * rr, 2 * rr], 'Curvature', [1 1], 'FaceColor', [0.2 0.3 0.9], 'EdgeColor', 'k'); %#ok<SAGROW>
                    hCn{i}(end + 1) = j; %#ok<SAGROW>
                end
            end
        end
        ht(i) = title(nm8(i), 'FontSize', 9);
    end
    stt = sgtitle('', 'FontSize', 11);
    annotation('textbox', [0.01 0 0.98 0.04], 'String', [foot '  Capsule drawing: counts scaled to the optimum (2-D proxy, not true 3-D packing).'], 'EdgeColor', 'none', 'FontSize', 7);
    for t = 1:nT
        for i = 1:nC + 1
            Rw = all8{i};
            for j = 1:10
                Tj = Rw.(sprintf('T_node%d_C', j))(t);
                set(hN{i}(j), 'FaceColor', interp1([25 45 60 75], cmapT, min(max(Tj, 25), 75)));
            end
            if i > 1
                fj = arrayfun(@(j) Rw.(sprintf('f_node%d', j))(t), 1:10);
                for q = 1:numel(hC{i}), set(hC{i}(q), 'FaceColor', (1 - fj(hCn{i}(q))) * [0.15 0.3 0.9] + fj(hCn{i}(q)) * [0.95 0.25 0.1]); end
            end
            set(ht(i), 'String', sprintf('%s\nmean %.1f C', nm8(i), Rw.T_w_mean_C(t)));
        end
        stt.String = sprintf('%s day, hour %d of %d   (water: blue 25 C -> red 75 C; capsules: blue solid -> red liquid)', kind, t - 1, nT);
        writeVideo(vw, getframe(fig));
    end
    close(vw); close(fig);
end

%% 6. Check: MATLAB arithmetic on the exported series
chk = check(check.case ~= "plain tank", :);
fprintf('M1 check: max |balance residual| over windows = %.2f %% of collector energy (kernel closure over the year: %.2g %%)\n', max(abs(chk.balance_resid_pct)), max(annual.residual_pct));
[~, rk_year] = sort(annual.paired_gain_window_kWh, 'descend');
fprintf('Annual ranking of criteria (best first): %s\n', mat2str(rk_year' - 1));
fprintf('M1 done. Figures in %s\n', fdir);
