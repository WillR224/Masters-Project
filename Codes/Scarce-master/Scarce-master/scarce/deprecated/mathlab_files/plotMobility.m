E = logspace(2,5,1000);
mu0_e = getMobility(E, 245, 0);
mu1_e = getMobility(E, 300, 0);
mu2_e = getMobility(E, 370, 0);
mu3_e = getMobility(E, 430, 0);
mu0_h = getMobility(E, 245, 1);
mu1_h = getMobility(E, 300, 1);
mu2_h = getMobility(E, 370, 1);
mu3_h = getMobility(E, 430, 1);
loglog(E,mu0_e, 'LineWidth', 1.2, 'color', 'black');
hold on;
loglog(E,mu1_e, 'LineWidth', 1.2, 'color', 'red');
loglog(E,mu2_e, 'LineWidth', 1.2, 'color', 'blue');
loglog(E,mu3_e, 'LineWidth', 1.2, 'color', 'green');
loglog(E,mu0_h, 'LineWidth', 1.2, 'color', 'black', 'LineStyle', '--');
loglog(E,mu1_h, 'LineWidth', 1.2, 'color', 'red', 'LineStyle', '--');
loglog(E,mu2_h, 'LineWidth', 1.2, 'color', 'blue', 'LineStyle', '--');
loglog(E,mu3_h, 'LineWidth', 1.2, 'color', 'green', 'LineStyle', '--');
hold off;
title('Charge carrier mobility in high purity silicon ', 'FontWeight','bold','FontSize', 10);
%title('Charge carrier velocity in high purity silicon ', 'FontWeight','bold','FontSize', 10);
xlabel('electric field [V/cm]', 'FontWeight','bold');
ylabel('electron/-hole mobility [cm^2/Vs]', 'FontWeight','bold');
%ylabel('electron/-hole velocity [cm/s]', 'FontWeight','bold');
set(gcf, 'Color', [1 1 1]);
ylim([5e1 5e3]);
%ylim([1e4 2e7]);
hleg1 = legend('T = 245 K','T = 300 K','T = 370 K','T = 430 K', 'Location', 'northeast');
%hleg1 = legend('T = 245 K','T = 300 K','T = 370 K','T = 430 K', 'Location', 'northwest');
grid on;
set(gca, 'GridLineStyle', '-');
export_fig('charge_carrier_mobility.pdf');
%export_fig('charge_carrier_velocity.pdf');