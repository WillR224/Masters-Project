E = logspace(2,5,1000);
v0 = getMobility(E, 245, 1) .* E;
v1 = getMobility(E, 300, 1) .* E;
v2 = getMobility(E, 370, 1) .* E;
v3 = getMobility(E, 430, 1) .* E;
loglog(E,v0, 'LineWidth', 2, 'color', 'black');
hold on;
loglog(E,v1, 'LineWidth', 2, 'color', 'red');
loglog(E,v2, 'LineWidth', 2, 'color', 'blue');
loglog(E,v3, 'LineWidth', 2, 'color', 'green');
hold off;
title('Electron drift velocity in high purity silicon ', 'FontWeight','bold','FontSize', 10);
xlabel('electric field [V/cm]', 'FontWeight','bold');
ylabel('electron drift velocity [cm/s]', 'FontWeight','bold');
set(gcf, 'Color', [1 1 1]);
hleg1 = legend('T = 245 K','T = 300 K','T = 370 K','T = 430 K', 'Position', [0.25, 0.25, .25, .25]);
grid on;